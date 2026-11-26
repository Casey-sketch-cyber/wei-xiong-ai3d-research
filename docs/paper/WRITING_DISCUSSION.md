# 写作讨论：数字太密与怎样写得更好

> Claude 发起，2026-11-26。作者认为正文数字太多、太密，读起来吃力，希望先和 Gemini 讨论怎样把文章写得更好，讨论的结论再写进论文写作 skill。

## 背景

- 统计结果：Results 各节每 100 个英文词有 17–35 个数字，§4.3 一节有 24 个置信区间；Introduction、Discussion 只有 1–7 个。详见 [可读性任务书](READABILITY_PASS.md)。
- 作者决定：先讨论，讨论定下来以后再写进论文写作 skill（`research-paper-story-writing`）。下面是 Claude 的初版草案，**还没有写进 skill**，请 Gemini 在第 4 题逐条表态。

### Claude 的初版草案（英文，供讨论）

Numbers in the text (keep the prose readable):
- The text says what happened and how large it was; the table holds the values. Do not copy a table row into a sentence.
- At most one headline number per claim, usually the primary metric's difference with one CI. Point to the table for secondary metrics and raw before/after values.
- At most one bracketed interval per sentence. Never chain several intervals in a row.
- Prefer ratios and plain words when they carry the point ("about a third lower"). In the text use 2–3 significant digits; keep full precision in the tables.
- State fixed settings (seeds, steps, strengths) once in Methods, then refer to them by name.
- The contribution list in the Introduction carries at most one number per item, and does not repeat the Abstract.
- Check density before submission: numbers per 100 words in each Results subsection, excluding tables, captions and citations. Above about 12, revise. Every number removed from the text must still appear in a table or the supplement.

## 请 Gemini 回答（直接写在下面“Gemini 的意见”里）

1. **诊断。** 除了数字太多，这篇稿子读起来吃力还有哪些原因？例如：术语和缩写多、句子太长、同一个设定反复描述、结论被埋在句子中间、各节之间的过渡不足。请举 2–3 个具体位置（节号和首句）。
2. **改写示范。** 选 §4.3 的第一段，写一版改写，把“改前 / 改后”并排列出。改后版本里保留的数字值都不能变。
3. **用图代替数字。** 有没有哪些区间更适合画成图，例如把各协议效应的配对差值和置信区间画成一张森林图（forest plot），放进正文或补充材料？请说说利弊；如果建议加图，由 Claude 负责画。
4. **补充规则。** 对上面 Claude 的初版草案，你同意哪些、反对哪些、还要补充什么？请写成可以直接放进 skill 的英文条目，每条一句话。
5. **其它写法建议。** 从审稿人的角度，这类评测论文（benchmark / evaluation study）怎样写才更好读、更有说服力？只写对这篇稿子用得上的。

## 规则

- 这一步只讨论，不改 `manuscript.tex`。
- 不新增实验，不改结论。
- 分支 `gemini/writing-discussion`。完成后请 Claude 审查；Claude 汇总双方一致的意见，交作者看过后再写进 skill，并更新可读性任务书，再由 Gemini 按定稿改法修订正文。

## Gemini 的意见

（待填写）
