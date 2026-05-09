# 大衍引擎 (DaYan Engine)

**基于《周易》梅花易数与六爻纳甲的战役判定引擎**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)

## 简介

大衍引擎是一个开源的游戏判定引擎，以《周易》六爻 + 梅花易数作为核心判定逻辑。
第一个演示是三国主题、AI agent 自动对战的赤壁之战战役模拟。

> "大衍之数五十，其用四十有九。" —— 《周易·系辞上》

## 特性

- **梅花易数起卦**: 任意数字输入 → 本卦 + 变卦 + 动爻
- **六爻纳甲推演**: 64 卦 × 384 爻 × 五行生克 × 六亲 × 世应
- **用神判定**: 用神得令/受克/有救/无救判定
- **分阶段战役**: 5 阶段 (开战/相持/决战/追击/善后)，每阶段起子卦
- **战报生成**: 三国演义风格中文战报
- **零外部依赖**: 核心引擎纯 Python 标准库
- **Agent 接口**: 为 LLM agent 预留接口（雏形用 mock）

## 快速开始

### 安装

```bash
# 无需安装，直接 clone 即可使用 (零外部依赖)
git clone <repo-url>
cd dayan-engine
```

### 运行赤壁之战 Demo

```bash
python3 dayan_engine/examples/chibi_demo.py

# 指定随机种子 (可复现)
python3 dayan_engine/examples/chibi_demo.py 42
```

### 运行测试

```bash
pip install pytest
python3 -m pytest dayan_engine/tests/ -v
```

## 项目结构

```
dayan_engine/
├── core/                       # 核心引擎 (纯本地, 零 LLM)
│   ├── types.py               # 数据类型: 八卦/爻/卦/战役配置
│   ├── wuxing.py              # 五行生克
│   ├── liuqin.py              # 六亲配位
│   ├── meihua.py              # 梅花易数起卦
│   ├── liuyao.py              # 六爻纳甲推演 (含64卦数据)
│   └── battle.py              # 战役判定引擎
├── factors/
│   └── battle_factors.py      # 12 因素 → 爻位映射 + 用神映射
├── narrator/
│   ├── template_narrator.py   # 模板填充战报生成器
│   └── templates/             # 战报模板库
├── agents/
│   └── mock_agent.py          # Mock agent (雏形)
├── examples/
│   └── chibi_demo.py          # 赤壁之战 demo
└── tests/                     # pytest 测试
```

## 核心算法

### 1. 梅花易数起卦

```
输入: (num1, num2, num3)
上卦 = num1 mod 8 (0→8 坤)
下卦 = num2 mod 8 (0→8 坤)
动爻 = (num1+num2+num3) mod 6 (0→6)
变卦 = 本卦在动爻位取反
```

八卦序: 乾1 兑2 离3 震4 巽5 坎6 艮7 坤8

### 2. 六爻纳甲 (京房法)

每爻配: 天干地支 + 五行 + 六亲 + 世应位

- **六亲**: 父母(生我) / 兄弟(同我) / 子孙(我生) / 妻财(我克) / 官鬼(克我)
- **世应**: 世爻为我方, 应爻为敌方, 相隔三位

### 3. 用神映射 (战役角色)

| 战役角色 | 用神 | 说明 |
|---------|------|------|
| 主帅 | 世爻/应爻 | 攻方世爻, 守方应爻 |
| 军师 | 兄弟爻 | 谋略决策 |
| 先锋 | 子孙爻 | 进攻杀伤 |
| 后勤 | 父母爻 | 粮草补给 |
| 军资 | 妻财爻 | 财力物资 |
| 敌将 | 官鬼爻 | 敌军威胁 |
| 谋士 | 应爻 | 敌情反映 |

### 4. 战果判定

- 用神得令 + 不受克 → 胜
- 用神受克且无救 → 败
- 子孙爻受克程度 → 伤亡比例
- 父母/妻财爻状态 → 后勤损失
- 动爻位置 → 关键转折点

### 5. 分阶段推演

```
阶段: 开战 → 相持 → 决战 → 追击 → 善后
每阶段基于总卦 + 前阶段累积 → 起子卦 → 用神判定
```

## 术语表 (Glossary)

| 中文 | 英文 | 解释 |
|------|------|------|
| 爻 | Line/Yao | 卦的基本单位, 分阴阳 |
| 卦 | Hexagram/Gua | 六爻组成, 共 64 种 |
| 八卦 | Eight Trigrams | 乾兑离震巽坎艮坤 |
| 五行 | Five Elements | 木火土金水 |
| 相生 | Generation | 木→火→土→金→水→木 |
| 相克 | Overcoming | 木→土→水→火→金→木 |
| 天干 | Heavenly Stems | 甲乙丙丁戊己庚辛壬癸 |
| 地支 | Earthly Branches | 子丑寅卯辰巳午未申酉戌亥 |
| 六亲 | Six Relations | 父母/兄弟/子孙/妻财/官鬼 |
| 世应 | Shi & Ying | 世爻(我), 应爻(彼) |
| 动爻 | Moving Line | 梅花起卦的变爻 |
| 用神 | Yongshen | 代表问卦核心事物的爻 |
| 纳甲 | Najia | 配天干地支于六爻 |
| 梅花易数 | Plum Blossom Yi | 宋代邵雍所创的起卦法 |
| 八宫 | Eight Palaces | 京房卦变体系 |
| 本卦 | Original Hex | 起卦所得原卦 |
| 变卦 | Changed Hex | 动爻取反后的新卦 |

## 开发

- **Python**: 3.11+
- **核心依赖**: 零
- **测试**: pytest
- **协议**: MIT

## 路线图

- [x] 梅花易数起卦
- [x] 六爻纳甲推演 (64卦全)
- [x] 五行生克 + 六亲配位
- [x] 战役判定引擎 (5阶段)
- [x] 模板战报生成器
- [x] 赤壁之战 demo
- [x] pytest 测试覆盖
- [ ] LLM agent 接入
- [ ] Web 界面
- [ ] 奇门遁甲模块
- [ ] 平衡性验证脚本

## License

MIT License - 详见 [LICENSE](LICENSE)
