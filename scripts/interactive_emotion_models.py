from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model_service.app.labels import MOODFLOW_LABELS
from model_service.app.predictor import EmotionPredictor


PROMPT_TEMPLATE = """你是一个中文情绪分类器。你只能从以下 8 个标签中选择 1 个，不能输出其他标签：
happy, calm, expecting, anxious, sad, irritable, plain, tired

标签说明：
- happy: 明确开心、喜悦、满足、轻松庆祝
- calm: 平静、稳定、安心、舒缓，没有明显兴奋或负担
- expecting: 期待、盼望、对未来有念想或兴奋等待
- anxious: 紧张、担心、不安、心慌、压力大
- sad: 难过、失落、委屈、低落、想哭
- irritable: 烦躁、生气、不耐烦、火大、容易炸
- plain: 普通、平淡、没有明显情绪起伏，只是在陈述日常
- tired: 疲惫、困、没精神、想休息、身体或脑力耗尽

判别规则：
1. 如果没有明显情绪线索，默认判为 plain，不要乱猜。
2. 只有出现“累、困、疲惫、想睡、熬夜、没精神、发烧、头疼、生病”等线索时，才能判 tired。
3. 只有明显出现“期待、盼望、等着、明天要发生好事、很想去做某事”等未来导向时，才能判 expecting。
4. calm 表示语气稳定、从容、安心，不等于普通陈述；普通陈述更接近 plain。
5. 如果同时有多个标签，选最主要、最显性的那个，不要解释成复杂组合。

示例：
文本：明天终于放假了，好开心
输出：{{"label":"happy","reason":"放假带来开心"}}

文本：想到明天出发旅行，我有点期待
输出：{{"label":"expecting","reason":"对未来有期待"}}

文本：想到明天汇报，我心里很慌
输出：{{"label":"anxious","reason":"明显紧张不安"}}

文本：今天就正常上课写作业，没什么特别的
输出：{{"label":"plain","reason":"普通日常陈述"}}

文本：连续加班两天，我只想睡觉
输出：{{"label":"tired","reason":"明显疲惫想休息"}}

请只输出一个 JSON 对象，格式如下：
{{"label":"<one_of_the_8_labels>","reason":"<不超过30字>"}}

文本：{text}
"""


@dataclass(frozen=True)
class ModelSpec:
    name: str
    kind: str
    target: str
    description: str


MODEL_SPECS = [
    ModelSpec("baseline-clean-v4", "artifact", "model_service/artifacts/baseline-clean-v4", "当前保留主模型：clean_v4 重训 baseline"),
    ModelSpec("baseline", "artifact", "model_service/artifacts/experiments/baseline", "归档实验：原始 TF-IDF + LogisticRegression"),
    ModelSpec("baseline-clean-v1", "artifact", "model_service/artifacts/experiments/baseline-clean-v1", "归档实验：clean_v1 重训 baseline"),
    ModelSpec("linear-svm-clean-v4", "artifact", "model_service/artifacts/experiments/linear-svm-clean-v4", "归档实验：clean_v4 的 TF-IDF + LinearSVC"),
    ModelSpec("transformer-rbt3-local", "artifact", "model_service/artifacts/experiments/transformer-rbt3-local", "归档实验：早期 rbt3 微调产物"),
    ModelSpec("transformer-rbt3-clean-v4", "artifact", "model_service/artifacts/experiments/transformer-rbt3-clean-v4", "归档实验：clean_v4 的 rbt3 微调"),
    ModelSpec("transformer-rbt6-clean-v4", "artifact", "model_service/artifacts/experiments/transformer-rbt6-clean-v4", "归档实验：clean_v4 的 rbt6 微调"),
    ModelSpec("qwen2.5-0.5b-prompt", "llm", "Qwen/Qwen2.5-0.5B-Instruct", "归档实验：本地小型开源大模型 + prompt"),
    ModelSpec("qwen2.5-1.5b-prompt", "llm", "Qwen/Qwen2.5-1.5B-Instruct", "归档实验：本地中小型开源大模型 + prompt"),
]


class PredictorLike(Protocol):
    def predict(self, text: str) -> dict[str, object]:
        ...


class LocalLLMPromptPredictor:
    def __init__(self, model_name: str, max_new_tokens: int = 40) -> None:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.model.eval()

    def predict(self, text: str) -> dict[str, object]:
        import torch

        prompt = PROMPT_TEMPLATE.format(text=text.strip())
        messages = [{"role": "user", "content": prompt}]
        rendered = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.tokenizer(rendered, return_tensors="pt")

        started = time.perf_counter()
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=None,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        latency_ms = (time.perf_counter() - started) * 1000

        generated = outputs[0][inputs["input_ids"].shape[1]:]
        raw_output = self.tokenizer.decode(generated, skip_special_tokens=True).strip()
        parsed = self._parse_output(raw_output)
        label = parsed["label"]

        return {
            "label": label,
            "display_name": label,
            "confidence": None,
            "probabilities": {},
            "reason": parsed.get("reason"),
            "raw_output": raw_output,
            "latency_ms": round(latency_ms, 2),
        }

    def _parse_output(self, raw_output: str) -> dict[str, str]:
        cleaned = raw_output.strip()
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
        try:
            payload = json.loads(cleaned)
            label = str(payload.get("label", "")).strip()
            if label in MOODFLOW_LABELS:
                return {
                    "label": label,
                    "reason": str(payload.get("reason", "")).strip(),
                }
        except json.JSONDecodeError:
            pass

        for label in MOODFLOW_LABELS:
            if re.search(rf"\b{re.escape(label)}\b", cleaned):
                return {"label": label, "reason": ""}
        return {"label": "plain", "reason": ""}


def available_specs() -> list[ModelSpec]:
    specs: list[ModelSpec] = []
    for spec in MODEL_SPECS:
        if spec.kind == "artifact":
            if (ROOT / spec.target).exists():
                specs.append(spec)
        else:
            specs.append(spec)
    return specs


def build_predictor(spec: ModelSpec) -> PredictorLike:
    if spec.kind == "artifact":
        predictor = EmotionPredictor(ROOT / spec.target)
        if not predictor.ready:
            raise SystemExit(f"Model artifact not ready: {spec.name} -> {spec.target}")
        return predictor
    return LocalLLMPromptPredictor(spec.target)


def print_models(specs: list[ModelSpec]) -> None:
    print("可用模型：")
    for idx, spec in enumerate(specs, start=1):
        print(f"  {idx}. {spec.name} - {spec.description}")


def choose_model(specs: list[ModelSpec]) -> ModelSpec:
    while True:
        print_models(specs)
        raw = input("请输入模型编号或名称：").strip()
        if not raw:
            continue
        if raw.isdigit():
            index = int(raw) - 1
            if 0 <= index < len(specs):
                return specs[index]
        for spec in specs:
            if raw == spec.name:
                return spec
        print("没匹配上，再试一次。")


def format_top3(result: dict[str, object]) -> str:
    probabilities = result.get("probabilities") or {}
    if not probabilities:
        return "N/A"
    top3 = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)[:3]
    return ", ".join(f"{label}:{score:.4f}" for label, score in top3)


def run_once(predictor: PredictorLike, text: str) -> None:
    started = time.perf_counter()
    result = predictor.predict(text)
    total_ms = (time.perf_counter() - started) * 1000

    print()
    print(f"输入: {text}")
    print(f"标签: {result.get('label')}")
    if result.get("display_name"):
        print(f"显示名: {result.get('display_name')}")
    if result.get("confidence") is not None:
        print(f"置信度: {float(result['confidence']):.4f}")
    print(f"Top3: {format_top3(result)}")
    if result.get("reason"):
        print(f"原因: {result.get('reason')}")
    if result.get("raw_output"):
        print(f"原始输出: {result.get('raw_output')}")
    latency = result.get("latency_ms")
    if latency is None:
        latency = round(total_ms, 2)
    print(f"耗时: {latency} ms")
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactively test trained emotion models on custom text.")
    parser.add_argument("--model", help="Model name from the built-in model list.")
    parser.add_argument("--text", help="Run a single prediction and exit.")
    parser.add_argument("--list", action="store_true", help="List available models and exit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    specs = available_specs()
    if args.list:
        print_models(specs)
        return

    if args.model:
        matched = next((spec for spec in specs if spec.name == args.model), None)
        if matched is None:
            raise SystemExit(f"Unknown model: {args.model}")
        spec = matched
    else:
        spec = specs[0]
        print(f"未指定模型，默认使用 {spec.name}。如需切换，传 --model，或先用 --list 查看可选模型。")

    print(f"\n已选择: {spec.name} - {spec.description}")
    predictor = build_predictor(spec)

    if args.text:
        run_once(predictor, args.text)
        return

    print("开始交互测试。输入空行或 exit 退出。")
    while True:
        text = input("请输入文本> ").strip()
        if not text or text.lower() in {"exit", "quit"}:
            break
        run_once(predictor, text)


if __name__ == "__main__":
    main()
