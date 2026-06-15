from pathlib import Path
import re

path = Path("backend/scripts/init_db.sql")
sql = path.read_text(encoding="utf-8")

# 备份原始文件
backup = path.with_suffix(".sql.bak")
backup.write_text(sql, encoding="utf-8")

# 1. 修复 IDENTITY + PRIMARY KEY 的达梦不兼容写法
sql = re.sub(
    r"(ID\s+BIGINT\s+)NOT\s+NULL\s+IDENTITY\s*\(\s*1\s*,\s*1\s*\)\s+PRIMARY\s+KEY\s*,",
    r"\1IDENTITY(1,1) NOT NULL,",
    sql,
    flags=re.IGNORECASE,
)

# 2. 给每个带 IDENTITY 的 CREATE TABLE 增加表级主键
table_pattern = re.compile(
    r"(CREATE\s+TABLE\s+\w+\s*\()(.*?)(\);)",
    flags=re.IGNORECASE | re.DOTALL,
)


def fix_table(match: re.Match) -> str:
    head = match.group(1)
    body = match.group(2)
    tail = match.group(3)

    has_identity_id = re.search(
        r"\bID\s+BIGINT\s+IDENTITY\s*\(\s*1\s*,\s*1\s*\)\s+NOT\s+NULL\s*,",
        body,
        flags=re.IGNORECASE,
    )

    has_primary_key = re.search(
        r"PRIMARY\s+KEY",
        body,
        flags=re.IGNORECASE,
    )

    if has_identity_id and not has_primary_key:
        body = body.rstrip()
        if not body.endswith(","):
            body += ","
        body += "\n    NOT CLUSTER PRIMARY KEY(ID)\n"

    return head + body + tail


sql = table_pattern.sub(fix_table, sql)

path.write_text(sql, encoding="utf-8")

print("已修复 backend/scripts/init_db.sql")
print(f"原文件备份为：{backup}")
