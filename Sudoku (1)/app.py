from flask import Flask, jsonify, request
from flask_cors import CORS
import random, copy
import clingo

app = Flask(__name__)
CORS(app)

solution = [['0' for _ in range(9)] for _ in range(9)]
grid = []
levels = { "easy": 25, "medium": 45, "hard": 60, "insane": 75 }

def is_valid(i, j, k, board):
    row = (i // 3) * 3
    col = (j // 3) * 3
    for it in range(9):
        if board[i][it] == k or board[it][j] == k or board[row + (it // 3)][col + (it % 3)] == k:
            return False
    return True

def solve(i, j, count):
    if count == 0:
        return 1
    sol_count = 0
    for x in range(i, 9):
        for y in range(j, 9):
            if grid[x][y] == '0':
                for k in map(str, range(1, 10)):
                    if is_valid(x, y, k, grid):
                        grid[x][y] = k
                        sol_count += solve(x, y, count - 1)
                        grid[x][y] = '0'
                    if sol_count > 1:
                        return sol_count
                return sol_count
        j = 0
    return sol_count

def remove_cells(k):
    global grid
    grid = copy.deepcopy(solution)
    ct = 1
    r = 40
    while k and r:
        row = random.randint(0, 8)
        col = random.randint(0, 8)
        removed = grid[row][col]
        grid[row][col] = '0'
        if solve(0, 0, ct) == 1:
            k -= 1
            ct += 1
        else:
            r -= 1
            grid[row][col] = removed

def generate_solution_with_clingo():
    asp_program = """
    size(1..9).
    1 { fill(X,Y,N) : size(N) } 1 :- size(X), size(Y).
    :- fill(X,Y1,N), fill(X,Y2,N), Y1 != Y2.
    :- fill(X1,Y,N), fill(X2,Y,N), X1 != X2.
    :- fill(X1,Y1,N), fill(X2,Y2,N), 
        (X1-1)/3 = (X2-1)/3, 
        (Y1-1)/3 = (Y2-1)/3, 
        (X1,Y1) != (X2,Y2).
    #show fill/3.
    """
    ctl = clingo.Control()
    ctl.add("base", [], asp_program)
    ctl.ground([("base", [])])
    result = [['0' for _ in range(9)] for _ in range(9)]
    def on_model(model):
        for atom in model.symbols(shown=True):
            if atom.name == "fill":
                x, y, n = map(lambda v: v.number, atom.arguments)
                result[x - 1][y - 1] = str(n)
    ctl.solve(on_model=on_model)
    return result

def get_hint_from_solution(solution, x, y):
    asp_facts = []
    for i in range(9):
        for j in range(9):
            val = int(solution[i][j])
            asp_facts.append(f"solution({i+1},{j+1},{val}).")

    asp_logic = f"""
    hint(N) :- solution({x+1}, {y+1}, N).
    #show hint/1.
    """

    asp_program = "\n".join(asp_facts) + "\n" + asp_logic

    ctl = clingo.Control()
    try:
        ctl.add("base", [], asp_program)
        ctl.ground([("base", [])])
    except RuntimeError as e:
        print(" Clingo parsing error:", e)
        print("ASP program that caused it:\n", asp_program)
        return None

    hint = None

    def on_model(model):
        nonlocal hint
        for atom in model.symbols(shown=True):
            if atom.name == "hint":
                hint = atom.arguments[0].number

    ctl.solve(on_model=on_model)
    return hint
@app.route('/hint', methods=['GET'])
def get_hint():
    try:
        x = int(request.args.get('x'))
        y = int(request.args.get('y'))

        if not (0 <= x <= 8 and 0 <= y <= 8):
            return jsonify({"error": "Invalid coordinates"}), 400

        hint = get_hint_from_solution(solution, x, y)
        if hint is not None:
            return jsonify({"x": x, "y": y, "hint": hint})
        else:
            return jsonify({"error": "Hint not found"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate', methods=['GET'])
def generate():
    level = request.args.get('level', 'easy')
    global solution
    solution = generate_solution_with_clingo()
    remove_cells(levels.get(level, 25))
    return jsonify({ 'solution': solution, 'grid': grid })

if __name__ == '__main__':
    app.run(debug=True)
