import abc
import dataclasses
import re
from enum import Enum
from typing import List, Tuple, Any


@dataclasses.dataclass
class PromptExpr(abc.ABC):
    weight: float

    @abc.abstractmethod
    def accept(self, visitor, *args, **kwargs) -> Any:
        pass


@dataclasses.dataclass
class LeafPrompt(PromptExpr):
    prompt: str

    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_leaf_prompt(self, *args, **kwargs)


@dataclasses.dataclass
class PerpPrompt(PromptExpr):
    children: List[PromptExpr]

    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_perp_prompt(self, *args, **kwargs)


class FlatSizeVisitor:
    def visit_leaf_prompt(self, that: LeafPrompt) -> int:
        return 1

    def visit_perp_prompt(self, that: PerpPrompt) -> int:
        return sum(child.accept(self) for child in that.children) if that.children else 0


def parse_root(string: str) -> PerpPrompt:
    tokens = tokenize(string)
    prompts = parse_prompts(tokens)
    return PerpPrompt(1., prompts)


def parse_prompts(tokens: List[str]) -> List[PromptExpr]:
    prompts = [parse_prompt(tokens)]
    while tokens:
        if tokens[0] in [']']:
            break

        prompts.append(parse_prompt(tokens, first=False))

    return prompts


def parse_prompt(tokens: List[str], first: bool = True) -> PromptExpr:
    if first:
        prompt_type = PromptKeyword.AND.value
    else:
        assert tokens[0] in prompt_keywords
        prompt_type = tokens.pop(0)

    if prompt_type == PromptKeyword.AND.value:
        prompt, weight = parse_prompt_text(tokens)
        return LeafPrompt(weight, prompt)
    else:
        if tokens[0] == '[':
            tokens.pop(0)
            prompts = parse_prompts(tokens)
            if tokens:
                assert tokens.pop(0) == ']'
            weight = parse_weight(tokens)
            return PerpPrompt(weight, prompts)
        else:
            prompt, weight = parse_prompt_text(tokens)
            return PerpPrompt(1., [LeafPrompt(weight, prompt)])


def parse_prompt_text(tokens: List[str]) -> Tuple[str, float]:
    text = ''
    depth = 0
    weight = 1.
    while tokens:
        if tokens[0] == ']':
            if depth == 0:
                break
            depth -= 1
        elif tokens[0] == '[':
            depth += 1
        elif tokens[0] == ':':
            if len(tokens) >= 2 and is_float(tokens[1].strip()):
                if len(tokens) < 3 or tokens[2] in prompt_keywords or tokens[2] == ']' and depth == 0:
                    tokens.pop(0)
                    weight = float(tokens.pop(0).strip())
                    break
        elif tokens[0] in prompt_keywords:
            break

        text += tokens.pop(0)

    return text, weight


def parse_weight(tokens: List[str]) -> float:
    weight = 1.
    if tokens and tokens[0] == ':':
        tokens.pop(0)
        if tokens:
            weight_str = tokens.pop(0)
            if is_float(weight_str):
                weight = float(weight_str)
    return weight


def tokenize(s: str):
    s = re.sub(r'\s+', ' ', s).strip()
    return [s for s in re.split(r'(\[|\]|:|\bAND_PERP\b|\bAND\b)', s) if s.strip()]


def is_float(string: str) -> bool:
    try:
        float(string)
        return True
    except ValueError:
        return False


class PromptKeyword(Enum):
    AND = 'AND'
    AND_PERP = 'AND_PERP'


prompt_keywords = [e.value for e in PromptKeyword]


if __name__ == '__main__':
    res = parse_root('''
    hello
    AND_PERP [
        arst
        AND defg : 2
        AND_PERP [
            very nested huh? what  [do you say :.0
        ]
    ]
    ''')
    pass
