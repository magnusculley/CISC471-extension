from collections.abc import Sequence
from pathlib import Path

from lark import Lark, Token, Transformer
from lark.visitors import v_args  # pyright: ignore[reportUnknownVariableType]

from .syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Boolean,
    Branch,
    Float,
    Identifier,
    Immediate,
    Let,
    LetRec,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
    Term,
    Tuple,
)


class AstTransformer(Transformer[Token, Program | Term]):
    def IDENTIFIER(self, token: Token) -> str:
        return str(token)

    def NUMBER(self, token: Token) -> int:
        return int(token)

    # pre processing functions that convert the tokens into the appropriate types for the AST nodes
    # Lark calls these itself when walks through the tree and then I don't have to manually convert everything

    @v_args(inline=True)
    def program(
        self,
        _program: Token,
        parameters: Sequence[Identifier],
        body: Term,
    ) -> Program:
        return Program(
            parameters=parameters,
            body=body,
        )

    def parameters(
        self,
        parameters: Sequence[Identifier],
    ) -> Sequence[Identifier]:
        return parameters

    @v_args(inline=True)
    def term(
        self,
        term: Term,
    ) -> Term:
        return term

    @v_args(inline=True)
    def let(
        self,
        _let: Token,
        bindings: Sequence[tuple[Identifier, Term]],
        body: Term,
    ) -> Term:
        return Let(
            bindings=bindings,
            body=body,
        )

    @v_args(inline=True)
    def letrec(
        self,
        _letrec: Token,
        bindings: Sequence[tuple[Identifier, Term]],
        body: Term,
    ) -> Term:
        return LetRec(
            bindings=bindings,
            body=body,
        )

    def bindings(
        self,
        bindings: Sequence[tuple[Identifier, Term]],
    ) -> Sequence[tuple[Identifier, Term]]:
        return bindings

    @v_args(inline=True)
    def binding(
        self,
        name: Identifier,
        value: Term,
    ) -> tuple[Identifier, Term]:
        return name, value

    @v_args(inline=True)
    def reference(
        self,
        name: Identifier,
    ) -> Term:
        return Reference(name=name)

    @v_args(inline=True)
    def abstract(
        self,
        _lambda: Token,
        parameters: Sequence[Identifier],
        body: Term,
    ) -> Term:
        return Abstract(
            parameters=parameters,
            body=body,
        )

    @v_args(inline=True)
    def apply(
        self,
        target: Term,
        *arguments: Term,
    ) -> Term:
        return Apply(
            target=target,
            arguments=list(arguments),
        )

    @v_args(inline=True)
    def immediate(
        self,
        value: int,
    ) -> Term:
        return Immediate(value=value)

    @v_args(inline=True)
    def primitive(
        self,
        operator: Token,
        left: Term,
        right: Term,
    ) -> Term:
        return Primitive(
            operator=str(operator),  # type: ignore
            left=left,
            right=right,
        )

    # I had to ignore the typing, because Pydantic is not convinced that that the generic string
    # adheres to the expectations of Primitive, but I know that it does because the grammar guarentees that it is one of the valid operators
    # I tried adding pre processing functions for OPERATOR and COMPARATOR, but that didn't work because then the type of operator would be str instead of Token, which is what the grammar expects
    # maybe it could be fixed by doing an explicit elif check in the primitive function, but that would be a lot of extra code and I don't think it matters that much

    @v_args(inline=True)
    def branch(
        self,
        _if: Token,
        operator: Token,
        left: Term,
        right: Term,
        consequent: Term,
        otherwise: Term,
    ) -> Term:
        return Branch(
            operator=str(operator),  # type: ignore
            left=left,
            right=right,
            consequent=consequent,
            otherwise=otherwise,
        )

    @v_args(inline=True)
    def allocate(
        self,
        _allocate: Token,
        count: Immediate,
    ) -> Term:
        return Allocate(count=count.value)

    @v_args(inline=True)
    def load(
        self,
        _load: Token,
        base: Term,
        index: Immediate,
    ) -> Term:
        return Load(
            base=base,
            index=index.value,
        )

    @v_args(inline=True)
    def store(
        self,
        _store: Token,
        base: Term,
        index: Immediate,
        value: Term,
    ) -> Term:
        return Store(
            base=base,
            index=index.value,
            value=value,
        )

    @v_args(inline=True)
    def begin(
        self,
        _begin: Token,
        *terms: Term,
    ) -> Term:
        return Begin(
            effects=list(terms[:-1]),
            value=terms[-1],
        )

    @v_args(inline=True)
    def float(
        self,
        value: float,
    ) -> Term:
        return Float(value=value)

    @v_args(inline=True)
    def boolean(
        self,
        value: bool,
    ) -> Term:
        return Boolean(value=value)

    @v_args(inline=True)
    def tuple(
        self,
        *elements: Term,
    ) -> Term:
        return Tuple(elements=list(elements))

    @v_args(inline=True)
    def index(
        self,
        _index: Token,
        tuple: Term,
        index: int,
    ) -> Term:
        return Index(tuple=tuple)


def parse_term(source: str) -> Term:
    grammar = Path(__file__).with_name("L3.lark").read_text()
    parser = Lark(grammar, start="term")
    tree = parser.parse(source)  # pyright: ignore[reportUnknownMemberType]
    return AstTransformer().transform(tree)  # pyright: ignore[reportReturnType]


def parse_program(source: str) -> Program:
    grammar = Path(__file__).with_name("L3.lark").read_text()
    parser = Lark(grammar, start="program")
    tree = parser.parse(source)  # pyright: ignore[reportUnknownMemberType]
    return AstTransformer().transform(tree)  # pyright: ignore[reportReturnType]
