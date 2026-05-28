from collections import Counter
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.archive import AiReport
from app.models.constants import TASK_ARCHIVED, TASK_COMPLETED
from app.repositories.ai_repository import AiReportRepository
from app.repositories.alarm_repository import AlarmRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.sensor_repository import SensorRepository
from app.schemas.ai_schema import AiReportOut


class AiService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.report_repo = AiReportRepository(db)
        self.experiment_repo = ExperimentRepository(db)
        self.sensor_repo = SensorRepository(db)
        self.alarm_repo = AlarmRepository(db)
        self.settings = get_settings()

    def _build_summary(self, experiment_id: int) -> dict[str, Any]:
        task = self.experiment_repo.get_by_id(experiment_id)
        if not task:
            raise HTTPException(status_code=404, detail="试验任务不存在")
        if task.status not in (TASK_COMPLETED, TASK_ARCHIVED):
            raise HTTPException(
                status_code=400,
                detail="仅已完成或已归档的试验可生成 AI 报告",
            )

        sensors = self.sensor_repo.list_recent_sensor(experiment_id, limit=500)
        alarms, _ = self.alarm_repo.list_alarms(experiment_id=experiment_id, page_size=100)

        speeds = [float(s.speed) for s in sensors if s.speed is not None]
        batteries = [float(s.battery) for s in sensors if s.battery is not None]
        resistances = [float(s.resistance) for s in sensors if s.resistance is not None]
        rolls = [float(s.roll) for s in sensors if s.roll is not None]

        alarm_types = Counter(a.alarm_type for a in alarms)
        alarm_desc = ", ".join(f"{k} {v}次" for k, v in alarm_types.items()) or "无"

        return {
            "exp_name": task.exp_name,
            "task_no": task.task_no,
            "status": task.status,
            "point_count": len(sensors),
            "max_speed": max(speeds) if speeds else 0,
            "min_battery": min(batteries) if batteries else 0,
            "max_resistance": max(resistances) if resistances else 0,
            "max_roll": max(rolls) if rolls else 0,
            "alarm_count": len(alarms),
            "alarm_summary": alarm_desc,
            "actual_start": task.actual_start_time,
            "actual_end": task.actual_end_time,
        }

    def _build_prompt(self, summary: dict[str, Any]) -> str:
        return f"""你是船舶与海洋工程试验分析专家。请根据以下试验结构化摘要，撰写试验分析报告。

试验名称：{summary['exp_name']}
任务单号：{summary['task_no']}
数据点数：{summary['point_count']}
最大速度：{summary['max_speed']:.2f} m/s
最低电量：{summary['min_battery']:.1f}%
最大阻力：{summary['max_resistance']:.1f} N
最大横摇角：{summary['max_roll']:.1f}°
告警数量：{summary['alarm_count']}
主要告警：{summary['alarm_summary']}

请用中文输出，分为两部分：
【试验概况与数据摘要】（约 200 字）
【异常分析、风险提示与改进建议】（约 300 字）
"""

    def _mock_response(self, summary: dict[str, Any]) -> tuple[str, str, str]:
        summary_text = (
            f"试验「{summary['exp_name']}」（{summary['task_no']}）已完成数据采集，"
            f"共记录 {summary['point_count']} 个采样点。"
            f"最大速度 {summary['max_speed']:.2f} m/s，最低电量 {summary['min_battery']:.1f}%，"
            f"最大阻力 {summary['max_resistance']:.1f} N。"
            f"试验过程中共产生 {summary['alarm_count']} 条告警（{summary['alarm_summary']}）。"
        )
        analysis_text = (
            "异常现象："
            + (
                f"告警以 {summary['alarm_summary']} 为主，需结合现场录像复核。"
                if summary["alarm_count"]
                else "本次试验未记录显著异常告警。"
            )
            + "\n可能原因：边界接近或速度波动可能与操船控制及水池流场有关。"
            "\n风险提示：若电量低于 20%，应提前返航更换电池。"
            "\n改进建议：后续可增加稳向板试验，并在低速段延长采样时间以提高阻力曲线分辨率。"
        )
        return (
            f"{summary['exp_name']} - AI 分析报告",
            summary_text,
            analysis_text,
        )

    def _parse_ai_content(self, content: str) -> tuple[str, str]:
        if "【异常分析" in content:
            parts = content.split("【异常分析", 1)
            summary = parts[0].replace("【试验概况与数据摘要】", "").strip()
            analysis = "【异常分析" + parts[1].strip()
            return summary, analysis
        mid = len(content) // 2
        return content[:mid].strip(), content[mid:].strip()

    async def _call_deepseek(self, prompt: str) -> tuple[str, str, str]:
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
        summary, analysis = self._parse_ai_content(content)
        title = "DeepSeek 试验分析报告"
        return title, summary, analysis

    async def generate(self, experiment_id: int, user_id: int) -> AiReportOut:
        summary = self._build_summary(experiment_id)
        prompt = self._build_prompt(summary)
        use_mock = self.settings.mock_ai or not self.settings.deepseek_api_key

        if use_mock:
            title, summary_text, analysis_text = self._mock_response(summary)
            model_name = "mock-local"
            is_mock = True
        else:
            title, summary_text, analysis_text = await self._call_deepseek(prompt)
            model_name = self.settings.deepseek_model
            is_mock = False

        existing = self.report_repo.get_by_experiment(experiment_id)
        if existing:
            self.report_repo.soft_delete(existing)

        report = AiReport(
            experiment_id=experiment_id,
            report_title=title,
            summary_text=summary_text,
            analysis_text=analysis_text,
            model_name=model_name,
            generated_by=user_id,
            is_deleted=0,
        )
        self.report_repo.create(report)
        self.db.commit()
        self.db.refresh(report)

        out = AiReportOut.model_validate(report)
        out.mock = is_mock
        return out

    def get_report(self, experiment_id: int) -> AiReportOut:
        report = self.report_repo.get_by_experiment(experiment_id)
        if not report:
            raise HTTPException(status_code=404, detail="尚未生成 AI 报告")
        out = AiReportOut.model_validate(report)
        out.mock = report.model_name == "mock-local"
        return out

    def delete_report(self, report_id: int) -> None:
        report = self.report_repo.get_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        self.report_repo.soft_delete(report)
        self.db.commit()
