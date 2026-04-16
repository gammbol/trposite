from solver.services.solvers.dispatcher import SolverDispatcher


def process_job(equation: str, variable: str = 'x', solver: str = 'sympy'):
    dispatcher = SolverDispatcher()

    result = dispatcher.solve(
        equation=equation,
        variable=variable,
        solver_name=solver
    )

    return result