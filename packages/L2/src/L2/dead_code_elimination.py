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
    Load,
    Primitive,
    Program,
    Reference,
    Store,
    Term,
    Tuple,
)


def is_pure(term: Term) -> bool:
    match term:
        case Let(bindings=bindings, body=body):
            return all(is_pure(value) for _, value in bindings) and is_pure(body)

        case Reference():
            return True

        case Immediate():
            return True

        case Allocate():
            return True

        case Abstract(body=body):
            return is_pure(body)

        case Apply():
            return False

        case Primitive(left=left, right=right):
            return is_pure(left) and is_pure(right)

        case Branch(left=left, right=right, consequent=consequent, otherwise=otherwise):
            return is_pure(left) and is_pure(right) and is_pure(consequent) and is_pure(otherwise)

        case Load(base=base):
            return is_pure(base)

        case Store():
            return False

        case Begin(effects=effects, value=value):  # pragma: no branch
            return all(is_pure(effect) for effect in effects) and is_pure(value)

        case Float():
            return True
        case Boolean():
            return True
        case Tuple(elements=elements):
            return all(is_pure(element) for element in elements)
        case Index(tuple=tuple, index=_index):
            return is_pure(tuple)


def is_referenced(term: Term, target: Identifier, bound: set[Identifier]) -> bool:
    match term:
        case Let(bindings=bindings, body=body):
            seen: set[Identifier] = set()

            for name, value in bindings:
                is_used = is_referenced(value, target, bound.union(seen))
                if is_used:
                    return True
                seen.add(name)

            return is_referenced(body, target, bound.union(seen))

        case Reference(name=name):
            if name in bound:
                return False
            return target == name

        case Abstract(parameters=parameters, body=body):
            return is_referenced(body, target, bound.union(set(parameters)))

        case Apply(target=target_term, arguments=arguments):
            if is_referenced(target_term, target, bound):
                return True

            for argument in arguments:
                if is_referenced(argument, target, bound):
                    return True

            return False

        case Immediate():
            return False

        case Allocate():
            return False

        case Primitive(left=left, right=right):
            return is_referenced(left, target, bound) or is_referenced(right, target, bound)

        case Branch(left=left, right=right, consequent=consequent, otherwise=otherwise):
            return (
                is_referenced(left, target, bound)
                or is_referenced(right, target, bound)
                or is_referenced(consequent, target, bound)
                or is_referenced(otherwise, target, bound)
            )

        case Load(base=base):
            return is_referenced(base, target, bound)

        case Store(base=base, value=value):
            return is_referenced(base, target, bound) or is_referenced(value, target, bound)

        case Begin(effects=effects, value=value):  # pragma: no branch
            if is_referenced(value, target, bound):
                return True

            for effect in effects:
                if is_referenced(effect, target, bound):
                    return True

            return False

        case Float():
            return False

        case Boolean():
            return False

        case Tuple(elements=elements):
            return any(is_referenced(element, target, bound) for element in elements)

        case Index(tuple=tuple, index=_index):
            return is_referenced(tuple, target, bound)


def dead_code_elimination_term(term: Term) -> Term:
    recur = dead_code_elimination_term

    match term:
        case Let(bindings=bindings, body=body):
            dce_body = recur(body)
            kept: list[tuple[Identifier, Term]] = []

            for name, value in reversed(bindings):
                dce_value = recur(value)
                used_by_body = is_referenced(dce_body, name, set())

                used_by_later_binding = False
                for _, kept_value in kept:
                    if is_referenced(kept_value, name, set()):
                        used_by_later_binding = True
                        break

                if used_by_body or used_by_later_binding:
                    kept.append((name, dce_value))
                    continue

                if not is_pure(dce_value):
                    kept.append((name, dce_value))

            kept.reverse()

            if not kept:
                return dce_body

            return Let(bindings=kept, body=dce_body)

        case Reference():
            return term

        case Immediate():
            return term

        case Allocate():
            return term

        case Abstract(parameters=parameters, body=body):
            return Abstract(parameters=parameters, body=recur(body))

        case Apply(target=target, arguments=arguments):
            return Apply(target=recur(target), arguments=[recur(argument) for argument in arguments])

        case Primitive(operator=operator, left=left, right=right):
            return Primitive(operator=operator, left=recur(left), right=recur(right))

        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return Branch(
                operator=operator,
                left=recur(left),
                right=recur(right),
                consequent=recur(consequent),
                otherwise=recur(otherwise),
            )

        case Load(base=base, index=index):
            return Load(base=recur(base), index=index)

        case Store(base=base, index=index, value=value):
            return Store(base=recur(base), index=index, value=recur(value))

        case Begin(effects=effects, value=value):  # pragma: no branch
            dce_effects = [recur(effect) for effect in effects]
            dce_effects = [effect for effect in dce_effects if not is_pure(effect)]
            dce_value = recur(value)

            if not dce_effects:
                return dce_value

            return Begin(effects=dce_effects, value=dce_value)

        case Float():
            return term

        case Boolean():
            return term

        case Tuple(elements=elements):
            return Tuple(elements=[recur(element) for element in elements])

        case Index(tuple=tuple, index=index):
            return Index(tuple=recur(tuple), index=index)


def dead_code_elimination_program(program: Program) -> Program:
    match program:
        case Program(parameters=parameters, body=body):  # pragma: no branch
            return Program(parameters=parameters, body=dead_code_elimination_term(body))
