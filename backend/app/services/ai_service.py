import time
from collections import Counter
from typing import Any, List, Optional

import httpx
from httpx import HTTPError, TimeoutException
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.archive import AiCallLog, AiReport
from app.models.constants import TASK_ARCHIVED, TASK_COMPLETED
from app.repositories.ai_log_repository import AiLogRepository
from app.repositories.ai_repository import AiReportRepository
from app.repositories.alarm_repository import AlarmRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.models.user import SysUser
from app.repositories.sensor_repository import SensorRepository
from app.services.audit_service import AuditService
from app.schemas.ai_schema import (
    ANALYSIS_TYPE_LABELS,
    AiCallLogOut,
    AiModeOut,
    AiReportListItem,
    AiReportOut,
    ExperimentDataSummary,
    ReportSection,
)
from app.schemas.common import PageResult
from app.utils.ai_report_utils import (
    parse_sections_from_content,
    parse_sections_from_stored,
    sections_to_text,
)


class AiService:

    def __init__(self, db: Session) -> None:
        self.db = db
        self.report_repo = AiReportRepository(db)
        self.log_repo = AiLogRepository(db)
        self.experiment_repo = ExperimentRepository(db)
        self.sensor_repo = SensorRepository(db)
        self.alarm_repo = AlarmRepository(db)
        self.settings = get_settings()

    def _display_model(self, model_name: Optional[str] = None) -> str:
        if not model_name or model_name == "mock-local":
            return self.settings.deepseek_model or "deepseek-chat"
        return model_name

    def _display_mode(self) -> str:
        return self.settings.deepseek_model or "DeepSeek API"

    def _use_mock(self) -> bool:
        has_key = bool((self.settings.deepseek_api_key or "").strip())
        return not has_key or self.settings.mock_ai

    def get_mode(self) -> AiModeOut:
        return AiModeOut(
            analysis_mode=self._display_mode(),
            mock_ai=self.settings.mock_ai,
            has_api_key=bool((self.settings.deepseek_api_key or "").strip()),
            model_name=self._display_model(),
        )

    def _analysis_focus(self, analysis_type: str) -> str:
        return ANALYSIS_TYPE_LABELS.get(analysis_type, ANALYSIS_TYPE_LABELS["OVERVIEW"])

    def _build_summary(self, experiment_id: int) -> dict[str, Any]:
        task = self.experiment_repo.get_by_id(experiment_id)
        if not task:
            raise HTTPException(status_code=404, detail="试验任务不存在")
        if task.status not in (TASK_COMPLETED, TASK_ARCHIVED):
            raise HTTPException(
                status_code=400,
                detail="仅已完成或已归档的试验可生成 AI 报告",
            )

        sensors = self.sensor_repo.list_sensor_series(experiment_id, 500)
        alarms, _ = self.alarm_repo.list_alarms(experiment_id=experiment_id, page_size=100)

        speeds = [float(s.speed) for s in sensors if s.speed is not None]
        batteries = [float(s.battery) for s in sensors if s.battery is not None]
        resistances = [float(s.resistance) for s in sensors if s.resistance is not None]
        rolls = [float(s.roll) for s in sensors if s.roll is not None]

        alarm_types = Counter(a.alarm_type for a in alarms)
        alarm_desc = ", ".join(f"{k} {v}次" for k, v in alarm_types.items()) or "无"

        return {
            "experiment_id": experiment_id,
            "exp_name": task.exp_name,
            "task_no": task.task_no,
            "status": task.status,
            "point_count": len(sensors),
            "max_speed": max(speeds) if speeds else None,
            "min_battery": min(batteries) if batteries else None,
            "max_resistance": max(resistances) if resistances else None,
            "max_roll": max(rolls) if rolls else None,
            "alarm_count": len(alarms),
            "alarm_summary": alarm_desc,
            "alarms": alarms,
            "actual_start": task.actual_start_time,
            "actual_end": task.actual_end_time,
        }

    def get_data_summary(self, experiment_id: int) -> ExperimentDataSummary:
        raw = self._build_summary(experiment_id)
        from app.schemas.ai_schema import AlarmBrief

        return ExperimentDataSummary(
            experiment_id=raw["experiment_id"],
            task_no=raw["task_no"],
            exp_name=raw["exp_name"],
            status=raw["status"],
            point_count=raw["point_count"],
            max_speed=raw["max_speed"],
            min_battery=raw["min_battery"],
            max_resistance=raw["max_resistance"],
            max_roll=raw["max_roll"],
            alarm_count=raw["alarm_count"],
            alarm_summary=raw["alarm_summary"],
            alarms=[
                AlarmBrief(
                    alarm_type=a.alarm_type,
                    alarm_message=a.alarm_message,
                    create_time=a.create_time,
                )
                for a in raw["alarms"][:10]
            ],
            actual_start_time=raw["actual_start"],
            actual_end_time=raw["actual_end"],
        )

    def _build_sections(
        self, summary: dict[str, Any], analysis_type: str
    ) -> List[ReportSection]:
        focus = self._analysis_focus(analysis_type)
        alarm_block = (
            f"- **告警数量**：{summary['alarm_count']} 条\n"
            f"- **主要类型**：{summary['alarm_summary']}"
            if summary["alarm_count"]
            else "本次试验未记录显著异常告警。"
        )
        cause_block = (
            f"告警以 **{summary['alarm_summary']}** 为主，可能与操船控制、流场扰动或传感器噪声有关。"
            if summary["alarm_count"]
            else "数据整体平稳，未发现明显异常模式。"
        )
        return [
            ReportSection(
                title="试验概况",
                content=(
                    f"试验 **{summary['exp_name']}**（`{summary['task_no']}`）已完成数据采集。\n\n"
                    f"- **分析类型**：{focus}\n"
                    f"- **数据状态**：可用于归档与复盘"
                ),
            ),
            ReportSection(
                title="关键数据",
                content=(
                    f"| 指标 | 数值 |\n| --- | --- |\n"
                    f"| 采样点 | {summary['point_count']} 个 |\n"
                    f"| 最大速度 | {summary['max_speed'] or 0:.2f} m/s |\n"
                    f"| 最低电量 | {summary['min_battery'] or 0:.1f}% |\n"
                    f"| 最大阻力 | {summary['max_resistance'] or 0:.1f} N |\n"
                    f"| 最大横摇 | {summary['max_roll'] or 0:.1f}° |"
                ),
            ),
            ReportSection(title="异常记录", content=alarm_block),
            ReportSection(title="可能原因", content=cause_block),
            ReportSection(
                title="改进建议",
                content=(
                    "1. 后续可增加稳向板对比试验，提高阻力曲线分辨率。\n"
                    "2. 在低速段延长采样时间，减少统计波动。\n"
                    "3. 对频繁告警类型建立阈值预警与现场复核流程。"
                ),
            ),
        ]

    def _build_prompt(self, summary: dict[str, Any], analysis_type: str = "OVERVIEW") -> str:
        focus = self._analysis_focus(analysis_type)
        return f"""请根据以下试验结构化摘要撰写中文分析报告。

分析类型：{focus}

试验名称：{summary['exp_name']}
任务单号：{summary['task_no']}
数据点数：{summary['point_count']}
最大速度：{summary['max_speed'] or 0:.2f} m/s
最低电量：{summary['min_battery'] or 0:.1f}%
最大阻力：{summary['max_resistance'] or 0:.1f} N
最大横摇角：{summary['max_roll'] or 0:.1f}°
告警数量：{summary['alarm_count']}
主要告警：{summary['alarm_summary']}

输出要求：
1. 严格分为五段，每段必须以【标题】开头，标题依次为：试验概况、关键数据、异常记录、可能原因、改进建议。
2. 每段正文使用 Markdown（可用列表、加粗、表格），基于给定数据客观分析，不要编造未提供的数值。
3. 不要输出代码块围栏外的多余说明，不要重复整段提示词。
"""

    async def _call_deepseek(
        self,
        prompt: str,
        analysis_type: str = "OVERVIEW",
        exp_name: str = "",
    ) -> tuple[str, str, str, Optional[int]]:
        base = self.settings.deepseek_base_url.rstrip("/")
        if base.endswith("/v1"):
            url = f"{base}/chat/completions"
        else:
            url = f"{base}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key.strip()}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.settings.deepseek_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是船舶与海洋工程湖海试验场数据分析专家。"
                        "输出专业、简洁的中文 Markdown 分析报告，严格遵循用户给出的分段格式。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.5,
            "max_tokens": 2048,
        }
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                resp = await client.post(url, headers=headers, json=body)
        except TimeoutException:
            raise HTTPException(status_code=504, detail="DeepSeek API 请求超时，请稍后重试")
        except HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"DeepSeek API 网络错误: {exc}")

        if resp.status_code != 200:
            detail = resp.text[:300].replace("\n", " ")
            raise HTTPException(
                status_code=502,
                detail=f"DeepSeek API 调用失败 ({resp.status_code}): {detail}",
            )

        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            raise HTTPException(status_code=502, detail="DeepSeek API 返回空结果")
        content = (choices[0].get("message") or {}).get("content") or ""
        if not content.strip():
            raise HTTPException(status_code=502, detail="DeepSeek API 返回内容为空")

        usage = data.get("usage", {})
        tokens = usage.get("total_tokens")
        sections = parse_sections_from_content(content)
        summary_text, analysis_text = sections_to_text(sections)
        focus = self._analysis_focus(analysis_type)
        title = f"{exp_name or '试验'} - {focus}" if exp_name else f"DeepSeek - {focus}"
        return title, summary_text, analysis_text, tokens

    def _write_call_log(
        self,
        experiment_id: int,
        analysis_type: str,
        model_name: str,
        is_mock: bool,
        success: bool,
        duration_ms: int,
        user_id: int,
        token_used: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        self.log_repo.create(
            AiCallLog(
                experiment_id=experiment_id,
                analysis_type=analysis_type,
                model_name=model_name,
                is_mock=1 if is_mock else 0,
                success=1 if success else 0,
                duration_ms=duration_ms,
                token_used=token_used,
                error_message=error_message,
                called_by=user_id,
            )
        )

    def _to_report_out(
        self, report: AiReport, is_mock: bool, analysis_type: Optional[str] = None
    ) -> AiReportOut:
        atype = analysis_type or report.analysis_type or "OVERVIEW"
        sections = parse_sections_from_stored(
            report.summary_text or "", report.analysis_text or ""
        )
        out = AiReportOut.model_validate(report)
        out.mock = False
        out.model_name = self._display_model(report.model_name)
        out.analysis_type = atype
        out.analysis_type_label = self._analysis_focus(atype)
        out.analysis_mode = self._display_mode()
        out.sections = sections
        return out

    async def generate(
        self, experiment_id: int, user: SysUser, analysis_type: str = "OVERVIEW"
    ) -> AiReportOut:
        user_id = user.id
        summary = self._build_summary(experiment_id)
        prompt = self._build_prompt(summary, analysis_type)
        use_mock = self._use_mock()
        start = time.monotonic()
        token_used: Optional[int] = None

        try:
            if use_mock:
                sections = self._build_sections(summary, analysis_type)
                summary_text, analysis_text = sections_to_text(sections)
                title = f"{summary['exp_name']} - {self._analysis_focus(analysis_type)}"
                model_name = "mock-local"
                is_mock = True
            else:
                title, summary_text, analysis_text, token_used = await self._call_deepseek(
                    prompt, analysis_type, summary["exp_name"]
                )
                model_name = self.settings.deepseek_model
                is_mock = False

            duration_ms = int((time.monotonic() - start) * 1000)

            existing = self.report_repo.get_by_experiment(experiment_id)
            if existing:
                self.report_repo.soft_delete(existing)

            report = AiReport(
                experiment_id=experiment_id,
                report_title=title,
                analysis_type=analysis_type,
                summary_text=summary_text,
                analysis_text=analysis_text,
                model_name=model_name,
                generated_by=user_id,
                is_deleted=0,
            )
            self.report_repo.create(report)
            self._write_call_log(
                experiment_id,
                analysis_type,
                model_name,
                is_mock,
                True,
                duration_ms,
                user_id,
                token_used,
            )
            self.db.commit()
            self.db.refresh(report)
            AuditService(self.db).log_user(
                user,
                "AI",
                "GENERATE",
                target_type="Experiment",
                target_id=experiment_id,
                detail=f"{analysis_type} / {model_name}",
            )
            return self._to_report_out(report, is_mock, analysis_type)
        except HTTPException as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._write_call_log(
                experiment_id,
                analysis_type,
                self.settings.deepseek_model,
                use_mock,
                False,
                duration_ms,
                user_id,
                error_message=str(exc.detail),
            )
            self.db.commit()
            raise

    def get_report(self, experiment_id: int) -> AiReportOut:
        report = self.report_repo.get_by_experiment(experiment_id)
        if not report:
            raise HTTPException(status_code=404, detail="尚未生成 AI 报告")
        is_mock = report.model_name == "mock-local"
        return self._to_report_out(report, is_mock)

    def list_reports(self, page: int = 1, page_size: int = 20) -> PageResult[AiReportListItem]:
        items, total = self.report_repo.list_reports(page, page_size)
        return PageResult(
            items=[AiReportListItem.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_call_logs(
        self,
        experiment_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageResult[AiCallLogOut]:
        items, total = self.log_repo.list_logs(experiment_id, page, page_size)
        return PageResult(
            items=[
                AiCallLogOut(
                    id=log.id,
                    experiment_id=log.experiment_id,
                    analysis_type=log.analysis_type,
                    model_name=log.model_name,
                    is_mock=log.is_mock == 1,
                    success=log.success == 1,
                    duration_ms=log.duration_ms,
                    token_used=log.token_used,
                    error_message=log.error_message,
                    call_time=log.call_time,
                )
                for log in items
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    def delete_report(self, report_id: int) -> None:
        report = self.report_repo.get_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        self.report_repo.soft_delete(report)
        self.db.commit()
