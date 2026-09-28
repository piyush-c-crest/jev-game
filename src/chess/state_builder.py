"""
state_builder.py - Converts Chess FEN, board position, and legal moves
into rich natural language state context for JEV System One.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional


PIECE_NAMES = {
    'p': 'pawn',
    'n': 'knight',
    'b': 'bishop',
    'r': 'rook',
    'q': 'queen',
    'k': 'king',
}

PIECE_VALUES = {
    'p': 1,
    'n': 3,
    'b': 3,
    'r': 5,
    'q': 9,
    'k': 0,
}

INITIAL_PIECES = {
    'p': 8,
    'n': 2,
    'b': 2,
    'r': 2,
    'q': 1,
    'k': 1,
}


@dataclass
class ChessPositionInfo:
    fen: str
    active_color: str  # "white" or "black"
    fullmove_number: int
    halfmove_clock: int
    castling_rights: str
    en_passant: str
    white_material: int
    black_material: int
    material_difference: int  # White - Black
    white_piece_counts: dict[str, int]
    black_piece_counts: dict[str, int]
    captured_by_white: list[str]
    captured_by_black: list[str]
    game_phase: str  # "Opening", "Middlegame", "Endgame"
    ascii_board: str


def parse_fen(fen: str) -> ChessPositionInfo:
    """Parse a FEN string into structured tactical and material data."""
    parts = fen.strip().split()
    board_part = parts[0] if len(parts) > 0 else "8/8/8/8/8/8/8/8"
    active_col = "white" if (len(parts) > 1 and parts[1] == 'w') else "black"
    castling = parts[2] if len(parts) > 2 else "-"
    ep = parts[3] if len(parts) > 3 else "-"
    halfmove = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
    fullmove = int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else 1

    white_counts = {'p': 0, 'n': 0, 'b': 0, 'r': 0, 'q': 0, 'k': 0}
    black_counts = {'p': 0, 'n': 0, 'b': 0, 'r': 0, 'q': 0, 'k': 0}

    rows = board_part.split('/')
    ascii_lines = []
    ascii_lines.append("    a b c d e f g h")

    for rank_idx, row in enumerate(rows):
        rank_num = 8 - rank_idx
        row_chars = []
        for ch in row:
            if ch.isdigit():
                row_chars.extend(['.'] * int(ch))
            else:
                row_chars.append(ch)
                lower_ch = ch.lower()
                if ch.isupper() and lower_ch in white_counts:
                    white_counts[lower_ch] += 1
                elif ch.islower() and lower_ch in black_counts:
                    black_counts[lower_ch] += 1

        ascii_lines.append(f"  {rank_num} {' '.join(row_chars)}  {rank_num}")

    ascii_lines.append("    a b c d e f g h")
    ascii_board = "\n".join(ascii_lines)

    white_mat = sum(white_counts[p] * PIECE_VALUES[p] for p in white_counts)
    black_mat = sum(black_counts[p] * PIECE_VALUES[p] for p in black_counts)
    mat_diff = white_mat - black_mat

    # Calculate captured pieces relative to standard 16 pieces
    captured_by_white = []  # Black pieces missing
    for p, init_cnt in INITIAL_PIECES.items():
        missing = init_cnt - black_counts.get(p, 0)
        for _ in range(max(0, missing)):
            captured_by_white.append(p.upper())

    captured_by_black = []  # White pieces missing
    for p, init_cnt in INITIAL_PIECES.items():
        missing = init_cnt - white_counts.get(p, 0)
        for _ in range(max(0, missing)):
            captured_by_black.append(p.lower())

    # Determine game phase
    total_major_minor = (
        white_counts['q'] + black_counts['q'] +
        white_counts['r'] + black_counts['r'] +
        white_counts['b'] + black_counts['b'] +
        white_counts['n'] + black_counts['n']
    )
    if fullmove <= 8 and total_major_minor >= 12:
        phase = "Opening"
    elif white_counts['q'] == 0 and black_counts['q'] == 0:
        phase = "Endgame"
    elif total_major_minor <= 6:
        phase = "Endgame"
    else:
        phase = "Middlegame"

    return ChessPositionInfo(
        fen=fen,
        active_color=active_col,
        fullmove_number=fullmove,
        halfmove_clock=halfmove,
        castling_rights=castling,
        en_passant=ep,
        white_material=white_mat,
        black_material=black_mat,
        material_difference=mat_diff,
        white_piece_counts=white_counts,
        black_piece_counts=black_counts,
        captured_by_white=captured_by_white,
        captured_by_black=captured_by_black,
        game_phase=phase,
        ascii_board=ascii_board,
    )


def describe_legal_move(move_obj: dict[str, Any] | str, color: str) -> str:
    """Generate a clear tactical explanation for a candidate chess move."""
    if isinstance(move_obj, str):
        san = move_obj
        from_sq = ""
        to_sq = ""
        piece = "p"
        captured = None
        flags = ""
    else:
        san = move_obj.get("san", "")
        from_sq = move_obj.get("from", "")
        to_sq = move_obj.get("to", "")
        piece = move_obj.get("piece", "p").lower()
        captured = move_obj.get("captured")
        flags = move_obj.get("flags", "")

    p_name = PIECE_NAMES.get(piece, "piece").capitalize()

    if san in ("O-O", "0-0"):
        return f"Castle kingside (O-O): tuck {color.capitalize()} King safely and activate rook into the game"
    elif san in ("O-O-O", "0-0-0"):
        return f"Castle queenside (O-O-O): secure King on queenside and connect rooks"
    elif captured:
        cap_name = PIECE_NAMES.get(str(captured).lower(), "piece")
        check_str = " delivering check" if "+" in san else ""
        return f"Tactical capture ({san}): {p_name} on {from_sq} captures {cap_name} on {to_sq} claiming material{check_str}"
    elif "+" in san:
        return f"Attacking check ({san}): {p_name} advances to {to_sq} delivering direct check to the enemy King"
    elif "=" in san:
        return f"Pawn promotion ({san}): pawn reaches the 8th rank to promote to Queen"
    elif piece == 'p':
        if to_sq in ('e4', 'd4', 'e5', 'd5'):
            return f"Central pawn stake ({san}): push pawn to {to_sq} controlling vital central territory"
        return f"Pawn push ({san}): advance pawn to {to_sq} gaining board space and controlling squares"
    elif piece in ('n', 'b'):
        if to_sq in ('f3', 'c3', 'f6', 'c6', 'e4', 'd4', 'e5', 'd5', 'c4', 'b5', 'g5', 'e7', 'd7'):
            return f"Piece development ({san}): deploy {p_name} to active square {to_sq} controlling key lines"
        return f"Maneuver {p_name} ({san}): reposition {p_name} to {to_sq}"
    elif piece == 'r':
        return f"Rook maneuver ({san}): bring Rook to {to_sq} to control or contest file"
    elif piece == 'q':
        return f"Queen centralization ({san}): maneuver Queen to {to_sq} asserting multi-diagonal influence"
    elif piece == 'k':
        return f"King move ({san}): reposition King to {to_sq} for safety or endgame activity"
    else:
        return f"Play move {san}: advance piece to {to_sq}"


def build_candidate_moves_criteria(
    legal_moves: list[dict[str, Any] | str],
    color: str,
    max_candidates: int = 35,
) -> dict[str, str]:
    """
    Construct a dictionary of candidate moves suitable for TypeSafe Choice question.
    Prioritizes tactical moves (captures, checks, promotions, castling, center control)
    if the legal move count is large.
    """
    if not legal_moves:
        return {}

    scored_moves: list[tuple[int, str, str]] = []

    for item in legal_moves:
        if isinstance(item, str):
            san = item
            desc = describe_legal_move(san, color)
            # Heuristic score
            score = 10
            if "x" in san:
                score += 30
            if "+" in san:
                score += 25
            if san in ("O-O", "O-O-O"):
                score += 20
            if any(sq in san for sq in ('e4', 'd4', 'e5', 'd5')):
                score += 15
        else:
            san = item.get("san", "")
            desc = describe_legal_move(item, color)
            score = 10
            if item.get("captured"):
                score += 30
            if "+" in san:
                score += 25
            if item.get("flags") in ('k', 'q'):
                score += 20
            to_sq = item.get("to", "")
            if to_sq in ('e4', 'd4', 'e5', 'd5'):
                score += 15

        scored_moves.append((score, san, desc))

    # Sort descending by priority
    scored_moves.sort(key=lambda x: x[0], reverse=True)

    # Take up to max_candidates
    chosen = scored_moves[:max_candidates]
    return {san: desc for _, san, desc in chosen}


def build_chess_context(
    fen: str,
    color: str,
    agent_name: str,
    agent_persona: str,
    recent_history: Optional[list[str]] = None,
    in_check: bool = False,
) -> str:
    """Build a natural language description of the chess board state for JEV."""
    info = parse_fen(fen)
    history_str = " ".join(recent_history[-8:]) if recent_history else "Game just began (Turn 1)."

    check_status = "CRITICAL ALERT: Your King is currently in CHECK! You must parry the check." if in_check else "King is secure (not in check)."

    if color == "white":
        mat_text = f"White material: {info.white_material} pts vs Black material: {info.black_material} pts (Diff: {'+' if info.material_difference > 0 else ''}{info.material_difference})."
    else:
        black_diff = -info.material_difference
        mat_text = f"Black material: {info.black_material} pts vs White material: {info.white_material} pts (Diff: {'+' if black_diff > 0 else ''}{black_diff})."

    return (
        f"I am {agent_name} playing as {color.upper()} in a competitive 1v1 Chess match.\n"
        f"My Tactical Identity: {agent_persona}.\n\n"
        f"Match State:\n"
        f"- Turn: Move {info.fullmove_number} ({color.upper()} to move)\n"
        f"- Game Phase: {info.game_phase}\n"
        f"- FEN: {fen}\n"
        f"- Tactical Alert: {check_status}\n"
        f"- Material Balance: {mat_text}\n"
        f"- Castling Rights: {info.castling_rights}\n"
        f"- En Passant Target: {info.en_passant}\n"
        f"- Recent Moves: {history_str}\n\n"
        f"Current Board Layout:\n"
        f"{info.ascii_board}\n\n"
        f"Objective:\n"
        f"Analyze the tactical position and determine the highest-quality move that develops pieces, "
        f"secures King safety, maintains central influence, and exploits opponent weaknesses."
    )
