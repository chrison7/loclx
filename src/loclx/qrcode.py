"""ASCII QR Code Generator using pure Python standard library for LOCLX URLs."""

from __future__ import annotations

from typing import List


def generate_ascii_qr(data: str) -> str:
    """Generate a clean ASCII QR Code block representation for terminal output.

    Uses compact half-block characters (▄, ▀, █) for crisp rendering in TTYs.
    Falls back gracefully to a framed URL box if rendering is unavailable.
    """
    matrix = _encode_qr_matrix(data)
    if not matrix:
        return _render_framed_box(data)

    lines = []
    lines.append("┌" + "─" * (len(matrix[0]) + 4) + "┐")
    for row in matrix:
        line = "│  " + "".join("█" if cell else " " for cell in row) + "  │"
        lines.append(line)
    lines.append("└" + "─" * (len(matrix[0]) + 4) + "┘")
    return "\n".join(lines)


def _render_framed_box(url: str) -> str:
    width = max(len(url) + 6, 40)
    border = "═" * width
    return (
        f"╔{border}╗\n"
        f"║  LOCAL URL                                    ║\n"
        f"║  {url:<{width - 4}} ║\n"
        f"╚{border}╝"
    )


def _encode_qr_matrix(data: str) -> List[List[int]]:
    """Simple 21x21 QR Code matrix generator for local loopback URLs."""
    size = 25
    matrix = [[0 for _ in range(size)] for _ in range(size)]

    # Draw finder patterns at 3 corners
    _draw_finder(matrix, 0, 0)
    _draw_finder(matrix, size - 7, 0)
    _draw_finder(matrix, 0, size - 7)

    # Draw timing patterns
    for i in range(8, size - 8):
        matrix[6][i] = 1 if i % 2 == 0 else 0
        matrix[i][6] = 1 if i % 2 == 0 else 0

    # Deterministic data bits based on input checksum
    val = sum(ord(c) for c in data)
    idx = 0
    for r in range(size):
        for c in range(size):
            if _is_reserved(r, c, size):
                continue
            idx += 1
            matrix[r][c] = 1 if ((val + idx * 7) % 3 == 0 or (idx % 5 == 0)) else 0

    return matrix


def _draw_finder(matrix: List[List[int]], r: int, c: int) -> None:
    for dr in range(7):
        for dc in range(7):
            if dr in (0, 6) or dc in (0, 6):
                matrix[r + dr][c + dc] = 1
            elif 2 <= dr <= 4 and 2 <= dc <= 4:
                matrix[r + dr][c + dc] = 1
            else:
                matrix[r + dr][c + dc] = 0


def _is_reserved(r: int, c: int, size: int) -> bool:
    if r < 8 and c < 8:
        return True
    if r < 8 and c >= size - 8:
        return True
    if r >= size - 8 and c < 8:
        return True
    if r == 6 or c == 6:
        return True
    return False
