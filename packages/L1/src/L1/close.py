from collections.abc import Mapping, Sequence

from L0 import syntax as L0

from . import syntax as L1

type ClosureContext = Mapping[L1.Identifier, tuple[L1.Identifier, Sequence[L1.Identifier]]]


def _merge_ordered(left: Sequence[L1.Identifier], right: Sequence[L1.Identifier]) -> list[L1.Identifier]:
    merged = list(left)
    seen = set(merged)

    for name in right:
        if name not in seen:
            merged.append(name)
            seen.add(name)

    return merged


def free_identifiers(statement: L1.Statement, bound: set[L1.Identifier]) -> list[L1.Identifier]:
    recur = free_identifiers

    match statement:
        case L1.Copy(destination=destination, source=source, then=then):
            used = [] if source in bound else [source]
            return _merge_ordered(used, recur(then, {destination, *bound}))

        case L1.Abstract(destination=destination, parameters=parameters, body=body, then=then):
            body_free = recur(body, {destination, *parameters, *bound})
            then_free = recur(then, {destination, *bound})
            return _merge_ordered(body_free, then_free)

        case L1.Apply(target=target, arguments=arguments):
            used: list[L1.Identifier] = (
                [] if target in bound else [target]
            )  # had a pylance issue with using used.append, so opted for this instead with explicit type annotation
            for argument in arguments:
                if argument not in bound and argument not in used:
                    used.append(argument)
            return used

        case L1.Immediate(destination=destination, then=then):
            return recur(then, {destination, *bound})

        case L1.Primitive(destination=destination, left=left, right=right, then=then):
            used: list[L1.Identifier] = []
            if left not in bound:
                used.append(left)
            if right not in bound and right not in used:
                used.append(right)
            return _merge_ordered(used, recur(then, {destination, *bound}))

        case L1.Branch(left=left, right=right, then=then, otherwise=otherwise):
            used: list[L1.Identifier] = []
            if left not in bound:
                used.append(left)
            if right not in bound and right not in used:
                used.append(right)
            then_free = recur(then, set(bound))
            otherwise_free = recur(otherwise, set(bound))
            return _merge_ordered(used, _merge_ordered(then_free, otherwise_free))

        case L1.Allocate(destination=destination, then=then):
            return recur(then, {destination, *bound})

        case L1.Load(destination=destination, base=base, then=then):
            used = [] if base in bound else [base]
            return _merge_ordered(used, recur(then, {destination, *bound}))

        case L1.Store(base=base, value=value, then=then):
            used: list[L1.Identifier] = []
            if base not in bound:
                used.append(base)
            if value not in bound and value not in used:
                used.append(value)
            return _merge_ordered(used, recur(then, set(bound)))

        case L1.Halt(value=value):
            return [] if value in bound else [value]

        case L1.Float(destination=destination, value=value, then=then):
            return recur(then, {destination, *bound})

        case L1.Boolean(destination=destination, value=value, then=then):
            return recur(then, {destination, *bound})

        case L1.Tuple(destination=destination, elements=elements, then=then):
            used: list[L1.Identifier] = []
            for element in elements:
                if element not in bound and element not in used:
                    used.append(element)
            return _merge_ordered(used, recur(then, {destination, *bound}))

        case L1.Index(destination=destination, tuple=tuple, index=_index, then=then):
            used: list[L1.Identifier] = []
            if tuple not in bound:
                used.append(tuple)
            return _merge_ordered(used, recur(then, {destination, *bound}))

        case _:  # pragma: no cover
            raise ValueError(statement)


def _without_names(
    context: ClosureContext, names: Sequence[L1.Identifier]
) -> dict[L1.Identifier, tuple[L1.Identifier, Sequence[L1.Identifier]]]:
    to_remove = set(names)
    return {name: info for name, info in context.items() if name not in to_remove}


def close_statement(
    statement: L1.Statement,
    context: ClosureContext,
    procedures: list[L0.Procedure],
) -> L0.Statement:
    recur = close_statement

    match statement:
        case L1.Copy(destination=destination, source=source, then=then):
            next_context = dict(context)
            if source in context:
                next_context[destination] = context[source]
            else:
                next_context.pop(destination, None)

            return L0.Copy(
                destination=destination,
                source=source,
                then=recur(then, next_context, procedures),
            )

        case L1.Abstract(destination=destination, parameters=parameters, body=body, then=then):
            free = free_identifiers(body, {destination, *parameters})
            procedure_name = destination

            body_context = _without_names(context, [destination, *parameters])
            body_context[destination] = (procedure_name, free)

            insertion_point = len(procedures)
            closed_body = recur(body, body_context, procedures)
            procedures.insert(
                insertion_point,
                L0.Procedure(
                    name=procedure_name,
                    parameters=[*free, *parameters],
                    body=closed_body,
                ),
            )

            next_context = dict(context)
            next_context[destination] = (procedure_name, free)

            return L0.Address(
                destination=destination,
                name=procedure_name,
                then=recur(then, next_context, procedures),
            )

        case L1.Apply(target=target, arguments=arguments):
            closure = context.get(target)
            closure_arguments = [] if closure is None else list(closure[1])
            return L0.Call(
                target=target,
                arguments=[*arguments, *closure_arguments],
            )

        case L1.Immediate(destination=destination, value=value, then=then):
            next_context = dict(context)
            next_context.pop(destination, None)
            return L0.Immediate(
                destination=destination,
                value=value,
                then=recur(then, next_context, procedures),
            )

        case L1.Primitive(destination=destination, operator=operator, left=left, right=right, then=then):
            next_context = dict(context)
            next_context.pop(destination, None)
            return L0.Primitive(
                destination=destination,
                operator=operator,
                left=left,
                right=right,
                then=recur(then, next_context, procedures),
            )

        case L1.Branch(operator=operator, left=left, right=right, then=then, otherwise=otherwise):
            return L0.Branch(
                operator=operator,
                left=left,
                right=right,
                then=recur(then, context, procedures),
                otherwise=recur(otherwise, context, procedures),
            )

        case L1.Allocate(destination=destination, count=count, then=then):
            next_context = dict(context)
            next_context.pop(destination, None)
            return L0.Allocate(
                destination=destination,
                count=count,
                then=recur(then, next_context, procedures),
            )

        case L1.Load(destination=destination, base=base, index=index, then=then):
            next_context = dict(context)
            next_context.pop(destination, None)
            return L0.Load(
                destination=destination,
                base=base,
                index=index,
                then=recur(then, next_context, procedures),
            )

        case L1.Store(base=base, index=index, value=value, then=then):
            return L0.Store(
                base=base,
                index=index,
                value=value,
                then=recur(then, context, procedures),
            )

        case L1.Halt(value=value):
            return L0.Halt(value=value)

        case L1.Float(destination=destination, value=value, then=then):
            next_context = dict(context)
            next_context.pop(destination, None)
            return L0.Float(
                destination=destination,
                value=value,
                then=recur(then, next_context, procedures),
            )

        case L1.Boolean(destination=destination, value=value, then=then):
            next_context = dict(context)
            next_context.pop(destination, None)
            return L0.Boolean(
                destination=destination,
                value=value,
                then=recur(then, next_context, procedures),
            )

        case L1.Tuple(destination=destination, elements=elements, then=then):
            next_context = dict(context)
            next_context.pop(destination, None)
            return L0.Tuple(
                destination=destination,
                elements=elements,
                then=recur(then, next_context, procedures),
            )

        case L1.Index(destination=destination, tuple=tuple, index=index, then=then):
            next_context = dict(context)
            next_context.pop(destination, None)
            return L0.Index(
                destination=destination,
                tuple=tuple,
                index=index,
                then=recur(then, next_context, procedures),
            )

        case _:  # pragma: no cover
            raise ValueError(statement)


def close_program(program: L1.Program) -> L0.Program:
    match program:
        case L1.Program(parameters=parameters, body=body):  # pragma: no branch
            procedures: list[L0.Procedure] = []
            closed_body = close_statement(body, {}, procedures)
            return L0.Program(
                procedures=[
                    L0.Procedure(name="l0", parameters=parameters, body=closed_body),
                    *procedures,
                ]
            )

        case _:  # pragma: no cover
            raise ValueError(program)
