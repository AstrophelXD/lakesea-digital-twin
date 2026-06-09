import csv
import io
import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.ai_repository import AiReportRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.sensor_repository import SensorRepository


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
        summary = report.summary_text or ""
        analysis = report.analysis_text or ""
        generated = report.generated_time.strftime("%Y-%m-%d %H:%M:%S")
        model = report.model_name or "unknown"

        if fmt == "html":
            content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <title>{title}</title>
  <style>
    body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; line-height: 1.6; }}
    h1 {{ color: #0f766e; }}
    h2 {{ border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; }}
    .meta {{ color: #6b7280; font-size: 14px; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="meta">任务 {task.task_no} · 模型 {model} · 生成于 {generated}</p>
  <h2>试验概况与关键数据</h2>
  <pre>{summary}</pre>
  <h2>分析与建议</h2>
  <pre>{analysis}</pre>
</body>
</html>"""
            return "text/html; charset=utf-8", f"{task.task_no}_ai_report.html", content

        content = f"""# {title}

> 任务：{task.task_no}  
> 模型：{model}  
> 生成时间：{generated}

## 试验概况与关键数据

{summary}

## 分析与建议

{analysis}
"""
        return "text/markdown; charset=utf-8", f"{task.task_no}_ai_report.md", content
