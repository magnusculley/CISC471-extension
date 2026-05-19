from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from functools import partial

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
    Index,
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


@dataclass(frozen=True)
class TypeUnknown:
    tag: str = "unknown"


@dataclass(frozen=True)
class TypeInt:
    tag: str = "int"


@dataclass(frozen=True)
class TypeFloat:
    tag: str = "float"


@dataclass(frozen=True)
class TypeBool:
    tag: str = "bool"


@dataclass(frozen=True)
class TypeTuple:
    elements: tuple["Type", ...]
    tag: str = "tuple"


@dataclass(frozen=True)
class TypeFunction:
    parameters: int
    returns: "Type"
    tag: str = "function"


@dataclass(frozen=True)
class TypeMemory:
    element: "Type"
    tag: str = "memory"


type Type = TypeUnknown | TypeInt | TypeFloat | TypeBool | TypeTuple | TypeFunction | TypeMemory
type Context = Mapping[Identifier, Type | None]


TYPE_UNKNOWN = TypeUnknown()
TYPE_INT = TypeInt()
TYPE_FLOAT = TypeFloat()
TYPE_BOOL = TypeBool()


def _type_of_name(name: Identifier, context: Context) -> Type:
    if name not in context:
        raise ValueError(f"unknown variable: {name}")

    value = context[name]
    if value is None:
        return TYPE_UNKNOWN

    return value


def _is_numeric(type_: Type) -> bool:
    return isinstance(type_, TypeInt | TypeFloat)


def _unify(left: Type, right: Type) -> Type:
    if isinstance(left, TypeUnknown):
        return right
    if isinstance(right, TypeUnknown):
        return left
    if left == right:
        return left
    if _is_numeric(left) and _is_numeric(right):
        if isinstance(left, TypeFloat) or isinstance(right, TypeFloat):
            return TYPE_FLOAT
        return TYPE_INT
    raise ValueError(f"type mismatch: {left} vs {right}")


def _expect_numeric(type_: Type, label: str) -> None:
    if isinstance(type_, TypeUnknown):
        return
    if not _is_numeric(type_):
        raise ValueError(f"{label} must be numeric")


def _expect_function(type_: Type) -> TypeFunction | None:
    if isinstance(type_, TypeFunction):
        return type_
    return None


def infer_term(
    term: Term,
    context: Context,
) -> Type:
    recur = partial(infer_term, context=context)

    match term:
        case Let(bindings=bindings, body=body):
            # duplicate names in let bindings are not allowed
            counts = Counter(name for name, _ in bindings)
            duplicates = {name: count for name, count in counts.items() if count > 1}
            if duplicates:
                raise ValueError(f"Duplicate binders in Let: {duplicates}")

            # check each binding value in the current context (recursive definitions not allowed)
            local: dict[Identifier, Type | None] = {}
            for name, value in bindings:
                local[name] = recur(value)

            # extend context and check the body last so that bound names are available
            return recur(body, context={**context, **local})

        case LetRec(bindings=bindings, body=body):
            counts = Counter(name for name, _ in bindings)
            duplicates = {name: count for name, count in counts.items() if count > 1}
            if duplicates:
                raise ValueError(f"Duplicate binders in LetRec: {duplicates}")

            for name, value in bindings:
                if not isinstance(value, Abstract):
                    raise ValueError("LetRec binding must be an Abstract (function) to be recursive")

            local: dict[Identifier, Type | None] = {
                name: TypeFunction(parameters=len(value.parameters), returns=TYPE_UNKNOWN) for name, value in bindings
            }

            for name, value in bindings:
                recur(value, context={**context, **local})

            return recur(body, context={**context, **local})

        case Reference(name=name):
            return _type_of_name(name, context)

        case Abstract(parameters=parameters, body=body):
            counts = Counter(parameters)
            dups = {name for name, count in counts.items() if count > 1}
            if dups:
                raise ValueError(f"Duplicate parameters in Abstract: {dups}")

            local = {parameter: TYPE_UNKNOWN for parameter in parameters}
            returns = recur(body, context={**context, **local})
            return TypeFunction(parameters=len(parameters), returns=returns)

        case Apply(target=target, arguments=arguments):
            target_type = recur(target)
            for argument in arguments:
                recur(argument)

            function_type = _expect_function(target_type)
            if function_type and function_type.parameters != len(arguments):
                raise ValueError(
                    f"apply arity mismatch: expected {function_type.parameters} arguments, got {len(arguments)}"
                )

            return function_type.returns if function_type else TYPE_UNKNOWN

        case Immediate(value=value):
            return TYPE_INT

        case Primitive(operator=_operator, left=left, right=right):
            left_type = recur(left)
            right_type = recur(right)
            _expect_numeric(left_type, "Primitive left operand")
            _expect_numeric(right_type, "Primitive right operand")
            return _unify(left_type, right_type)

        case Branch(operator=_operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            left_type = recur(left)
            right_type = recur(right)
            _ = _unify(left_type, right_type)

            consequent_type = recur(consequent)
            otherwise_type = recur(otherwise)
            return _unify(consequent_type, otherwise_type)

        case Allocate(count=count):
            count_type = TYPE_INT if isinstance(count, int) else recur(count)
            _expect_numeric(count_type, "Allocate count")
            return TypeMemory(element=TYPE_UNKNOWN)

        case Load(base=base, index=_index):
            base_type = recur(base)
            if isinstance(base_type, TypeUnknown):
                return TYPE_UNKNOWN
            if not isinstance(base_type, TypeMemory):
                raise ValueError("Load base must be memory")
            return base_type.element

        case Store(base=base, index=_index, value=value):
            base_type = recur(base)
            value_type = recur(value)
            if isinstance(base_type, TypeUnknown):
                return TYPE_INT
            if not isinstance(base_type, TypeMemory):
                raise ValueError("Store base must be memory")
            _ = _unify(base_type.element, value_type)
            return TYPE_INT

        case Begin(effects=effects, value=value):  # pragma: no branch
            for effect in effects:
                recur(effect)
            return recur(value)

        case Float(value=value):
            return TYPE_FLOAT

        case Boolean(value=value):
            return TYPE_BOOL

        case Tuple(elements=elements):
            return TypeTuple(elements=tuple(recur(element) for element in elements))

        case Index(tuple=tuple_term, index=_index):
            tuple_type = recur(tuple_term)
            if isinstance(tuple_type, TypeUnknown):
                return TYPE_UNKNOWN
            if not isinstance(tuple_type, TypeTuple):
                raise ValueError("Index target must be a tuple")
            if _index >= len(tuple_type.elements):
                raise ValueError(f"Tuple index out of bounds: {_index} for size {len(tuple_type.elements)}")
            return tuple_type.elements[_index]


def check_term(
    term: Term,
    context: Context,
) -> None:
    infer_term(term, context)


def check_program(
    program: Program,
) -> None:
    match program:
        case Program(parameters=parameters, body=body):  # pragma: no branch
            counts = Counter(parameters)
            duplicates = {name for name, count in counts.items() if count > 1}
            if duplicates:
                raise ValueError(f"Duplicate parameters in program: {duplicates}")

            local = dict.fromkeys(parameters, None)
            check_term(body, context=local)
