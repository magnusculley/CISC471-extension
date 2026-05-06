from .constant_folding import constant_folding_program
from .constant_propagation import constant_propagation_program
from .dead_code_elimination import dead_code_elimination_program
from .syntax import Program


def optimize_program(
    program: Program,
) -> Program:
    current = program
    while True:
        optimized = dead_code_elimination_program(
            constant_folding_program(
                constant_propagation_program(current),
            )
        )
        #I do wonder if this will cause an infinite loop if the optimizations keep changing back and forth, but it hasn't happened yet, and I don't think it could, but if anything breaks later on it is probably this
        if optimized == current:
            return optimized

        current = optimized
