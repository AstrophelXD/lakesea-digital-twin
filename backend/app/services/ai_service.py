import time
from collections import Counter
from typing import Any, List, Optional

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.archive import AiCallLog, AiReport
from app.models.constants import TASK_ARCHIVED, TASK_COMPLETED
from app.repositories.ai_log_repository import AiLogRepository
from app.repositories.ai_repository import AiReportRepository
from app.repositories.alarm_repository import AlarmRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.sensor_repository import SensorRepository
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


class AiService:
    SECTION_TITLES = [
        "试验概况",
        "关键数据",
        "异常记录",
        "可能原因",
        "改进建议",
    ]

    def __init__(self, db: Session) -> None:
        self.db = db
        self.report_repo = AiReportRepository(db)
        self.log_repo = AiLogRepository(db)
        self.experiment_repo = ExperimentRepository(db)
        self.sensor_repo = SensorRepository(db)
        self.alarm_repo = AlarmRepository(db)
        self.settings = get_settings()

    def get_mode(self) -> AiModeOut:
        use_mock = self.settings.mock_ai or not self.settings.deepseek_api_key
        return AiModeOut(
            analysis_mode="Mock" if use_mock else "DeepSeek API",
            mock_ai=self.settings.mock_ai,
            has_api_key=bool(self.settings.deepseek_api_key),
            model_name=self.settings.deepseek_model if not use_mock else "mock-local",
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
        return [
            ReportSection(
                title="试验概况",
                content=(
                    f"试验「{summary['exp_name']}」（{summary['task_no']}）已完成数据采集，"
                    f"分析类型：{focus}。"
                ),
            ),
            ReportSection(
                title="关键数据",
                content=(
                    f"采样点 {summary['point_count']} 个；"
                    f"最大速度 {summary['max_speed'] or 0:.2f} m/s；"
                    f"最低电量 {summary['min_battery'] or 0:.1f}%；"
                    f"最大阻力 {summary['max_resistance'] or 0:.1f} N；"
                    f"最大横摇 {summary['max_roll'] or 0:.1f}°。"
                ),
            ),
            ReportSection(
                title="异常记录",
                content=(
                    f"共 {summary['alarm_count']} 条告警：{summary['alarm_summary']}。"
                    if summary["alarm_count"]
                    else "本次试验未记录显著异常告警。"
                ),
            ),
            ReportSection(
                title="可能原因",
                content=(
                    f"告警以 {summary['alarm_summary']} 为主，可能与操船控制、流场扰动或传感器噪声有关。"
                    if summary["alarm_count"]
                    else "数据整体平稳，未发现明显异常模式。"
                ),
            ),
            ReportSection(
                title="改进建议",
                content=(
                    "建议后续增加稳向板对比试验，并在低速段延长采样时间以提高阻力曲线分辨率；"
                    "对频繁告警类型建立阈值预警策略。"
                ),
            ),
        ]

    def _sections_to_text(self, sections: List[ReportSection]) -> tuple[str, str]:
        summary_parts = [s for s in sections if s.title in ("试验概况", "关键数据", "异常记录")]
        analysis_parts = [s for s in sections if s.title in ("可能原因", "改进建议")]
        summary_text = "\n\n".join(f"【{s.title}】\n{s.content}" for s in summary_parts)
        analysis_text = "\n\n".join(f"【{s.title}】\n{s.content}" for s in analysis_parts)
        return summary_text, analysis_text

    def _parse_sections_from_text(
        self, summary_text: str, analysis_text: str
    ) -> List[ReportSection]:
        sections: List[ReportSection] = []
        for block in (summary_text or "").split("【"):
            if "】" not in block:
                continue
            title, content = block.split("】", 1)
            sections.append(ReportSection(title=title.strip(), content=content.strip()))
        for block in (analysis_text or "").split("【"):
            if "】" not in block:
                continue
            title, content = block.split("】", 1)
            sections.append(ReportSection(title=title.strip(), content=content.strip()))
        return sections or [
            ReportSection(title="试验概况与数据摘要", content=summary_text or ""),
            ReportSection(title="分析与建议", content=analysis_text or ""),
        ]

    def _build_prompt(self, summary: dict[str, Any], analysis_type: str = "OVERVIEW") -> str:
        focus = self._analysis_focus(analysis_type)
        return f"""你是船舶与海洋工程试验分析专家。请根据以下试验结构化摘要，撰写试验分析报告。
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

请用中文输出，严格分为五段，每段以【标题】开头：
【试验概况】
【关键数据】
【异常记录】
【可能原因】
【改进建议】
"""

    async def _call_deepseek(
        self, prompt: str, analysis_type: str = "OVERVIEW"
    ) -> tuple[str, str, str, Optional[int]]:
        url = f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.settings.deepseek_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"DeepSeek API 调用失败: {resp.text[:200]}",
                )
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens = usage.get("total_tokens")
        sections = self._parse_sections_from_text(content, "")
        if len(sections) <= 2:
            sections = self._parse_sections_from_text(content, content)
        summary_text, analysis_text = self._sections_to_text(sections)
        title = f"DeepSeek - {self._analysis_focus(analysis_type)}"
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
        sections = self._parse_sections_from_text(
            report.summary_text or "", report.analysis_text or ""
        )
        out = AiReportOut.model_validate(report)
        out.mock = is_mock
        out.analysis_type = atype
        out.analysis_type_label = self._analysis_focus(atype)
        out.analysis_mode = "Mock" if is_mock else "DeepSeek API"
        out.sections = sections
        return out

    async def generate(
        self, experiment_id: int, user_id: int, analysis_type: str = "OVERVIEW"
    ) -> AiReportOut:
        summary = self._build_summary(experiment_id)
        prompt = self._build_prompt(summary, analysis_type)
        use_mock = self.settings.mock_ai or not self.settings.deepseek_api_key
        start = time.monotonic()
        token_used: Optional[int] = None

        try:
            if use_mock:
                sections = self._build_sections(summary, analysis_type)
                summary_text, analysis_text = self._sections_to_text(sections)
                title = f"{summary['exp_name']} - {self._analysis_focus(analysis_type)}"
                model_name = "mock-local"
                is_mock = True
            else:
                title, summary_text, analysis_text, token_used = await self._call_deepseek(
                    prompt, analysis_type
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
