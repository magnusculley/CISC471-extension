# noqa: F841
from collections.abc import Mapping
from functools import partial

from L2 import syntax as L2

from . import syntax as L3

type Context = Mapping[L3.Identifier, bool]


def eliminate_letrec_term(
    term: L3.Term,
    context: Context,
) -> L2.Term:
    recur = partial(eliminate_letrec_term, context=context)

    match term:
        case L3.Let(bindings=bindings, body=body):
            local = {
                name: (isinstance(value, L3.Reference) and bool(context.get(value.name, False)))
                for name, value in bindings
            }
            return L2.Let(
                bindings=[(name, recur(value)) for name, value in bindings],
                body=recur(body, context={**context, **local}),
            )

        case L3.LetRec(bindings=bindings, body=body):
            local = dict.fromkeys([name for name, _ in bindings], True)
            return L2.Let(
                bindings=[(name, L2.Allocate(count=2)) for name, _ in bindings],
                body=L2.Begin(
                    effects=[
                        *[
                            L2.Store(
                                base=L2.Reference(name=name),
                                index=0,
                                value=recur(value, context={**context, **local}),
                            )
                            for name, value in bindings
                        ],
                        *[
                            L2.Store(
                                base=L2.Reference(name=name),
                                index=1,
                                value=L2.Reference(name=name),
                            )
                            for name, _ in bindings
                        ],
                    ],
                    value=recur(body, context={**context, **local}),
                ),
            )

        case L3.Reference(name=name):
            return L2.Reference(name=name)

        case L3.Abstract(parameters=parameters, body=body):
            return L2.Abstract(
                parameters=parameters,
                body=recur(body),
            )

        case L3.Apply(target=L3.Reference(name=name), arguments=arguments) if context.get(name, False):
            closure = L2.Reference(name=name)
            return L2.Apply(
                target=L2.Load(base=closure, index=0),
                arguments=[
                    L2.Load(base=closure, index=1),
                    *[recur(argument) for argument in arguments],
                ],
            )

        case L3.Apply(target=target, arguments=arguments):
            return L2.Apply(target=recur(target), arguments=[recur(argument) for argument in arguments])

        case L3.Immediate(value=value):
            return L2.Immediate(value=value)

        case L3.Primitive(operator=operator, left=left, right=right):
            return L2.Primitive(
                operator=operator,
                left=recur(left),
                right=recur(right),
            )

        case L3.Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return L2.Branch(
                operator=operator,
                left=recur(left),
                right=recur(right),
                consequent=recur(consequent),
                otherwise=recur(otherwise),
            )

        case L3.Allocate(count=count):
            return L2.Allocate(count=count)

        case L3.Load(base=base, index=index):
            return L2.Load(
                base=recur(base),
                index=index,
            )

        case L3.Store(base=base, index=_index, value=value):
            return L2.Store(
                base=recur(base),
                index=_index,
                value=recur(value),
            )

        case L3.Begin(effects=effects, value=value):  # pragma: no branch
            return L2.Begin(
                effects=[recur(effect) for effect in effects],
                value=recur(value),
            )

        case L3.Float(value=value):
            return L2.Float(value=value)

        case L3.Boolean(value=value):
            return L2.Boolean(value=value)

        case Tuple(elements=elements):
            return L2.Tuple(elements=[recur(element) for element in elements])

        case L3.Index(tuple=tuple, index=index):
            return L2.Index(tuple=recur(tuple), index=index)


def eliminate_letrec_program(
    program: L3.Program,
) -> L2.Program:
    match program:
        case L3.Program(parameters=parameters, body=body):  # pragma: no branch
            return L2.Program(
                parameters=parameters,
                body=eliminate_letrec_term(body, {}),
            )
