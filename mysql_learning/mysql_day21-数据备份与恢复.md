# 🐬 今日MySQL学习 · Day 21/30
**主题**：数据备份与恢复

---

## 【学习目标】

- 掌握 mysqldump 逻辑备份的全量/单库/单表用法
- 理解 binlog 二进制日志的作用，学会基于 binlog 的增量恢复
- 了解物理备份（xtrabackup）的概念与适用场景
- 建立完整的备份策略思维（全量+增量+定时+异地）

---

## 【核心语法】

### 1. mysqldump — 逻辑备份工具

```sql
-- 全库备份（所有数据库）
mysqldump -u root -p --all-databases > all_db_backup.sql

-- 单库备份
mysqldump -u root -p dinosaur_island > dinosaur_backup.sql

-- 单表备份
mysqldump -u root -p dinosaur_island players > players_backup.sql

-- 多表备份
mysqldump -u root -p dinosaur_island players dinosaurs battle_records > core_tables_backup.sql

-- 带建库语句的备份（恢复时自动 CREATE DATABASE）
mysqldump -u root -p --databases dinosaur_island > db_with_create.sql

-- 只备份表结构（不含数据）
mysqldump -u root -p --no-data dinosaur_island players > players_schema.sql

-- 只备份数据（不含表结构）
mysqldump -u root -p --no-create-info dinosaur_island players > players_data.sql
```

### 2. mysqldump 常用参数

```sql
-- --single-transaction：InnoDB一致性备份，不锁表（推荐）
mysqldump -u root -p --single-transaction dinosaur_island > backup_safe.sql

-- --quick：大表逐行输出，不一次性加载到内存
mysqldump -u root -p --quick dinosaur_island > backup_quick.sql

-- --routines：同时备份存储过程和函数
mysqldump -u root -p --routines --single-transaction dinosaur_island > backup_full.sql

-- --triggers：同时备份触发器（默认已包含，可显式指定）
mysqldump -u root -p --triggers dinosaur_island > backup_with_triggers.sql

-- --master-data=2：在备份中记录 binlog 位置（注释形式），用于增量恢复定位
mysqldump -u root -p --master-data=2 --single-transaction dinosaur_island > backup_with_binlog_pos.sql

-- --where：只导出满足条件的数据（单表时可用）
mysqldump -u root -p dinosaur_island players --where="level >= 50" > high_level_players.sql

-- --compress：压缩传输（减少网络带宽，本地备份效果有限）
mysqldump -u root -p --compress dinosaur_island > backup_compressed.sql
```

### 3. SQL 文件恢复

```sql
-- 恢复全库/单库备份
mysql -u root -p < all_db_backup.sql
mysql -u root -p dinosaur_island < dinosaur_backup.sql

-- 恢复单表（需要先确保目标库和表结构存在，或用 --databases 备份）
mysql -u root -p dinosaur_island < players_backup.sql

-- source 命令（在 MySQL 客户端内执行）
mysql> USE dinosaur_island;
mysql> SOURCE /path/to/players_backup.sql;
```

### 4. binlog — 二进制日志（增量备份核心）

```sql
-- 查看 binlog 是否开启
SHOW VARIABLES LIKE 'log_bin';
-- ON = 已开启

-- 查看 binlog 文件列表
SHOW BINARY LOGS;

-- 查看当前正在写入的 binlog 文件
SHOW MASTER STATUS;
-- 返回：File | Position | Binlog_Do_DB | Binlog_Ignore_DB

-- 查看 binlog 内容（事件格式）
SHOW BINLOG EVENTS IN 'mysql-bin.000001';

-- 用 mysqlbinlog 工具解析 binlog（命令行）
mysqlbinlog mysql-bin.000001 > binlog_events.sql
mysqlbinlog --start-position=154 --stop-position=500 mysql-bin.000001 > partial_recovery.sql

-- 基于时间范围的增量恢复
mysqlbinlog --start-datetime="2026-06-24 10:00:00" \
            --stop-datetime="2026-06-24 14:00:00" \
            mysql-bin.000001 > time_range_recovery.sql

-- 执行增量恢复
mysql -u root -p < partial_recovery.sql
```

### 5. binlog 配置（my.ini / my.cnf）

```ini
# 开启 binlog
[mysqld]
log-bin=mysql-bin
binlog_format=ROW        # ROW/STATEMENT/MIXED，推荐 ROW
expire_logs_days=7       # binlog 保留天数
max_binlog_size=100M     # 单个 binlog 文件最大大小
server-id=1              # 必须设置，否则 binlog 不生效
```

### 6. PURGE — 清理过期 binlog

```sql
-- 删除指定编号之前的所有 binlog
PURGE BINARY LOGS TO 'mysql-bin.000010';

-- 删除指定时间之前的 binlog
PURGE BINARY LOGS BEFORE '2026-06-20 00:00:00';

-- 自动清理（由 expire_logs_days 控制，无需手动）
```

---

## 【实战示例】

### 示例 1：基础全量备份与恢复演练

**场景**：测试环境每天自动备份，今天手动演练一次完整流程

```sql
-- Step 1: 先准备一些测试数据
CREATE DATABASE IF NOT EXISTS backup_test;
USE backup_test;

CREATE TABLE test_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_name VARCHAR(50),
    score INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO test_scores (player_name, score) VALUES
('阿克', 9500), ('涂伟富', 8800), ('小明', 7200);

SELECT * FROM test_scores;
-- 确认数据存在

-- Step 2: 执行全库备份（命令行）
-- mysqldump -u root -p --single-transaction --databases backup_test > backup_test_full.sql

-- Step 3: 模拟"灾难"——误删数据
DELETE FROM test_scores WHERE player_name = '小明';
SELECT * FROM test_scores;  -- 小明没了

-- Step 4: 恢复
-- mysql -u root -p < backup_test_full.sql

-- Step 5: 验证恢复结果
SELECT * FROM test_scores;  -- 小明回来了！

-- Step 6: 清理
DROP DATABASE backup_test;
```

### 示例 2：全量 + binlog 增量恢复

**场景**：凌晨做了全量备份，上午 10 点有人误操作 DROP TABLE，需要恢复到误操作前的状态

```sql
-- Step 1: 假设凌晨 2:00 已做全量备份（带 binlog 位置）
-- mysqldump -u root -p --single-transaction --master-data=2 \
--   --databases dinosaur_island > daily_full.sql

-- 备份文件头部会有注释：
-- CHANGE MASTER TO MASTER_LOG_FILE='mysql-bin.000015', MASTER_LOG_POS=154;
-- 这告诉我们：全量备份对应 binlog 的起始位置

-- Step 2: 查看 binlog 状态
SHOW MASTER STATUS;
-- File: mysql-bin.000015, Position: 2030

-- Step 3: 找到误操作的位置（用 mysqlbinlog 解析）
-- mysqlbinlog mysql-bin.000015 | grep -n "DROP TABLE"
-- 发现 DROP TABLE 在 Position 1890

-- Step 4: 先恢复全量
-- mysql -u root -p < daily_full.sql

-- Step 5: 再用 binlog 增量恢复（从全量备份点 → 误操作前）
-- mysqlbinlog --start-position=154 --stop-position=1890 \
--   mysql-bin.000015 > incremental_before_drop.sql
-- mysql -u root -p dinosaur_island < incremental_before_drop.sql

-- Step 6: 验证数据完整性
SELECT COUNT(*) FROM players;
SELECT COUNT(*) FROM dinosaurs;
```

### 示例 3：测试人员的备份验证自动化（Python + mysqldump）

**场景**：作为测试人员，每次版本发布前需要验证备份流程是否正常，写一个 Python 脚本自动化检查

```python
import subprocess
import os
import datetime
import pymysql

class BackupValidator:
    """数据库备份验证器 - 测试人员必备"""

    def __init__(self, host='localhost', user='root', password='',
                 database='dinosaur_island', backup_dir='./backups'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)

    def full_backup(self):
        """执行全量备份"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.backup_dir}/{self.database}_full_{timestamp}.sql"

        cmd = [
            'mysqldump',
            f'-u{self.user}',
            f'-p{self.password}' if self.password else '',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--master-data=2',
            self.database
        ]
        # 过滤空参数
        cmd = [c for c in cmd if c]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ 备份失败: {result.stderr}")
            return None

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(result.stdout)

        size_mb = os.path.getsize(filename) / 1024 / 1024
        print(f"✅ 备份成功: {filename} ({size_mb:.2f} MB)")
        return filename

    def verify_backup_integrity(self, backup_file):
        """验证备份文件完整性"""
        issues = []

        with open(backup_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查1: 备份文件是否有 MySQL dump header
        if 'MySQL dump' not in content:
            issues.append("缺少 mysqldump 头部标识")

        # 检查2: 是否包含 CREATE TABLE 语句
        create_count = content.count('CREATE TABLE')
        if create_count == 0:
            issues.append("缺少 CREATE TABLE 语句")

        # 检查3: 是否包含 INSERT 语句
        insert_count = content.count('INSERT INTO')
        if insert_count == 0:
            issues.append("缺少 INSERT 数据语句")

        # 检查4: 是否有 binlog 位置记录
        if 'MASTER_LOG_POS' in content:
            print("✅ 包含 binlog 位置信息，可用于增量恢复")
        else:
            issues.append("缺少 binlog 位置信息（增量恢复不可用）")

        # 检查5: 文件末尾是否有完成标记
        if 'Dump completed on' not in content:
            issues.append("缺少完成标记，备份可能不完整")

        if issues:
            print(f"⚠️ 验证发现问题:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print(f"✅ 备份文件完整性验证通过 (表:{create_count}, 数据:{insert_count})")
            return True

    def test_backup_and_restore(self):
        """完整备份恢复测试流程"""
        print("=" * 50)
        print("🧪 数据库备份恢复测试开始")
        print("=" * 50)

        # 1. 记录当前数据状态
        conn = pymysql.connect(
            host=self.host, user=self.user,
            password=self.password, database=self.database
        )
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM players")
        original_count = cursor.fetchone()[0]
        print(f"📊 原始玩家数: {original_count}")

        # 2. 执行备份
        backup_file = self.full_backup()
        if not backup_file:
            return False

        # 3. 验证备份完整性
        if not self.verify_backup_integrity(backup_file):
            return False

        # 4. 恢复测试（可选：在测试库中恢复验证）
        print("💡 恢复验证步骤：")
        print("  mysql -u root -p -e 'CREATE DATABASE restore_test'")
        print(f"  sed 's/dinosaur_island/restore_test/g' {backup_file} > restore_test.sql")
        print("  mysql -u root -p restore_test < restore_test.sql")
        print("  然后对比原始库和恢复库的数据一致性")

        cursor.close()
        conn.close()
        print("=" * 50)
        print("✅ 备份恢复测试完成")
        return True


# 使用示例
if __name__ == '__main__':
    validator = BackupValidator(
        host='localhost',
        user='root',
        password='your_password',
        database='dinosaur_island'
    )
    validator.test_backup_and_restore()
```

---

## 【注意事项/易错点】

### 1. mysqldump 常见坑

- **锁表问题**：默认 mysqldump 会锁表（MyISAM），InnoDB 用 `--single-transaction` 可避免锁表，生产环境必须加
- **字符集问题**：备份和恢复时字符集不一致会导致乱码，建议加 `--default-character-set=utf8mb4`
- **大表备份慢**：百万级数据 mysqldump 可能要几十分钟，考虑用 `--quick` 或改用物理备份

### 2. binlog 增量恢复注意

- **binlog 必须提前开启**：如果没开 log_bin，增量恢复无从谈起。部署时就应配置好
- **恢复顺序**：先全量 → 再增量，增量之间按 binlog 文件编号顺序执行
- **stop-position 精确定位**：需要仔细分析 binlog 找到误操作的精确位置，否则可能恢复过头
- **ROW 格式的 binlog 可读性差**：`mysqlbinlog` 默认输出的是 ROW 格式的伪 SQL，加 `--base64-output=DECODE-ROWS -v` 才能看到可读 SQL

### 3. 备份策略提醒

- **逻辑备份 vs 物理备份**：
  - 逻辑备份（mysqldump）：灵活、可读、跨版本，但大库慢
  - 物理备份（xtrabackup）：快、热备，但文件不可读，恢复时需准备阶段
- **备份不是存了就完事**：定期验证恢复流程，否则灾难时才发现备份不可用
- **异地存储**：备份只放在同一台服务器 = 没备份。至少备份到另一台机器或云存储

---

## 【今日练习题】

### 练习 1：手动备份恢复演练（必做）

在你的本地 MySQL 中执行以下操作：

1. 创建一个数据库 `backup_lab`，建一张表 `hero_stats`（含 id/name/level/power），插入 5 条数据
2. 用 mysqldump 做全量备份，保存到文件
3. 删除 `hero_stats` 表中的 2 条数据（模拟误操作）
4. 用备份文件恢复
5. 验证数据是否恢复完整

> 提示：用 `--single-transaction --databases backup_lab > backup_lab.sql`

### 练习 2：检查你的 MySQL binlog 配置（扩展）

1. 执行 `SHOW VARIABLES LIKE 'log_bin';` 看是否开启
2. 如果未开启，找到你的 `my.ini`（Windows）配置文件路径：`SELECT @@datadir;`
3. 在 `my.ini` 的 `[mysqld]` 下添加 `log-bin=mysql-bin` 和 `server-id=1`
4. 重启 MySQL 服务，再次检查 `log_bin` 是否变为 ON
5. 执行一些 INSERT/UPDATE，然后用 `SHOW MASTER STATUS` 和 `SHOW BINLOG EVENTS` 观察变化

---

## 【一句话总结】

**备份是数据库的保险，全量保底、binlog 增量保细节、定期验证保信心——不验证的备份等于没备份。**
