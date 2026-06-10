import csv
import io
import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.ai_repository import AiReportRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.sensor_repository import SensorRepository
from app.utils.ai_report_utils import (
    markdown_to_html,
    parse_sections_from_stored,
    sections_to_markdown,
)


class ArchiveExportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.experiment_repo = ExperimentRepository(db)
        self.sensor_repo = SensorRepository(db)
        self.ai_repo = AiReportRepository(db)

    def _get_task_or_404(self, task_id: int):
        task = self.experiment_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="试验任务不存在")
        return task

    def export_sensor_csv(self, task_id: int) -> tuple[str, str]:
        task = self._get_task_or_404(task_id)
        rows = self.sensor_repo.list_sensor_series(task_id, 5000)
        if not rows:
            raise HTTPException(status_code=404, detail="暂无传感器数据可导出")

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "timestamp",
                "position_x",
                "position_y",
                "speed",
                "heading",
                "roll",
                "pitch",
                "battery",
                "resistance",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    r.position_x,
                    r.position_y,
                    r.speed,
                    r.heading,
                    r.roll,
                    r.pitch,
                    r.battery,
                    r.resistance,
                ]
            )
        filename = f"{task.task_no}_sensor.csv"
        return filename, buffer.getvalue()

    def export_track_json(self, task_id: int) -> tuple[str, str]:
        task = self._get_task_or_404(task_id)
        tracks = self.sensor_repo.list_tracks(task_id, 5000)
        if not tracks:
            raise HTTPException(status_code=404, detail="暂无轨迹数据可导出")

        payload = {
            "taskId": task.id,
            "taskNo": task.task_no,
            "expName": task.exp_name,
            "exportedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pointCount": len(tracks),
            "tracks": [
                {
                    "timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "positionX": float(t.position_x or 0),
                    "positionY": float(t.position_y or 0),
                    "heading": float(t.heading) if t.heading is not None else None,
                }
                for t in tracks
            ],
        }
        filename = f"{task.task_no}_track.json"
        return filename, json.dumps(payload, ensure_ascii=False, indent=2)

    def export_ai_report(self, task_id: int, fmt: str = "markdown") -> tuple[str, str, str]:
        task = self._get_task_or_404(task_id)
        report = self.ai_repo.get_by_experiment(task_id)
        if not report:
            raise HTTPException(status_code=404, detail="尚未生成 AI 报告，请先在 AI 分析页生成")

        title = report.report_title or f"{task.exp_name} - AI Report"
        generated = report.generated_time.strftime("%Y-%m-%d %H:%M:%S")
        model = report.model_name or "unknown"
        sections = parse_sections_from_stored(
            report.summary_text or "", report.analysis_text or ""
        )
        body_md = sections_to_markdown(sections)

        if fmt == "html":
            section_html = "\n".join(
                f"<section class=\"block\"><h2>{sec.title}</h2>"
                f"{markdown_to_html(sec.content)}</section>"
                for sec in sections
            )
            content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <title>{title}</title>
  <style>
    body {{ font-family: "Segoe UI", sans-serif; max-width: 860px; margin: 2rem auto; line-height: 1.7; color: #374151; }}
    h1 {{ color: #0f766e; margin-bottom: 0.25rem; }}
    h2 {{ color: #0f766e; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-top: 1.5rem; }}
    .meta {{ color: #6b7280; font-size: 14px; margin-bottom: 1.5rem; }}
    .block {{ margin-bottom: 1rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 0.5rem 0; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 6px 10px; text-align: left; }}
    th {{ background: #f3f4f6; }}
    code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 4px; }}
    ul, ol {{ padding-left: 1.25rem; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="meta">任务 {task.task_no} · 模型 {model} · 生成于 {generated}</p>
  {section_html}
</body>
</html>"""
            return "text/html; charset=utf-8", f"{task.task_no}_ai_report.html", content

        content = f"""# {title}

> 任务：{task.task_no}  
> 模型：{model}  
> 生成时间：{generated}

{body_md}
"""
        return "text/markdown; charset=utf-8", f"{task.task_no}_ai_report.md", content
