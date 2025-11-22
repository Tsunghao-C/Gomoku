"""
Utility functions shared across the Gomoku game modules.
"""


def get_line_string(r, c, dr, dc, board, player, opponent, board_size):
    """
    Gets a string representation of a line passing through (r,c) in direction (dr,dc).
    'P' = Player, 'O' = Opponent, 'E' = Empty, 'X' = Out of bounds
    NOTE: board is 1D array now.
    """
    line = [''] * 31
    for i in range(-15, 16):
        cr, cc = r + dr * i, c + dc * i
        idx = i + 15
        if not (0 <= cr < board_size and 0 <= cc < board_size):
            line[idx] = 'X'
        else:
            piece = board[cr * board_size + cc]
            if piece == 0:  # EMPTY
                line[idx] = 'E'
            elif piece == player:
                line[idx] = 'P'
            elif piece == opponent:
                line[idx] = 'O'
    return "".join(line)


def get_line_values(r, c, dr, dc, board, player, opponent, board_size):
    """
    Gets a numerical representation of a line passing through (r,c).
    Values: 0=Empty, 1=Player, 2=Opponent, 3=OutOfBounds
    Returns a list of integers.
    NOTE: board is 1D array now.
    """
    line = [0] * 13
    for i in range(-6, 7):
        cr, cc = r + dr * i, c + dc * i
        idx = i + 6
        if not (0 <= cr < board_size and 0 <= cc < board_size):
            line[idx] = 3  # X
        else:
            piece = board[cr * board_size + cc]
            if piece == 0:
                line[idx] = 0  # E
            elif piece == player:
                line[idx] = 1  # P
            elif piece == opponent:
                line[idx] = 2  # O
    return line


def get_line_coords(r, c, dr, dc, board_size):
    """
    Gets the coordinates of all points in a line passing through (r,c).
    Used for deduplication in full board evaluation.
    """
    coords = []
    for i in range(-4, 5):
        cr, cc = r + dr * i, c + dc * i
        if 0 <= cr < board_size and 0 <= cc < board_size:
            coords.append((cr, cc))
    return coords
