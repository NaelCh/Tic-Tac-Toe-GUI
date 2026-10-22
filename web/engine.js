/** Rules and computer opponents shared by the browser interface and tests. */
export const LINES = Object.freeze([
  [0, 1, 2], [3, 4, 5], [6, 7, 8],
  [0, 3, 6], [1, 4, 7], [2, 5, 8],
  [0, 4, 8], [2, 4, 6],
].map((line) => Object.freeze(line)));

const PREFERRED_CELLS = [4, 0, 2, 6, 8, 1, 3, 5, 7];
const DIFFICULTIES = new Set(['easy', 'medium', 'hard', 'unbeatable']);
const values = new Map();
const opposite = (turn) => turn === 'X' ? 'O' : 'X';

export function winningLine(board) {
  return LINES.find(([a, b, c]) => board[a] && board[a] === board[b] && board[a] === board[c]) ?? [];
}

export function outcome(board) {
  const line = winningLine(board);
  if (line.length) return board[line[0]];
  return board.every(Boolean) ? 'draw' : null;
}

function afterMove(board, cell, turn) {
  const next = board.slice();
  next[cell] = turn;
  return next;
}

function value(board, turn) {
  const result = outcome(board);
  if (result) return result === 'draw' ? 0 : result === turn ? 1 : -1;
  const key = `${turn}:${board.map((cell) => cell || '-').join('')}`;
  if (values.has(key)) return values.get(key);
  let score = -Infinity;
  for (let cell = 0; cell < 9; cell += 1) {
    if (!board[cell]) {
      score = Math.max(score, -value(afterMove(board, cell, turn), opposite(turn)));
      if (score === 1) break;
    }
  }
  values.set(key, score);
  return score;
}

/** Return an optimal move, preferring center, then corners when scores tie. */
export function bestMove(board, turn) {
  if (outcome(board)) return null;
  let best = null;
  let bestScore = -Infinity;
  for (const cell of PREFERRED_CELLS) {
    if (board[cell]) continue;
    const score = -value(afterMove(board, cell, turn), opposite(turn));
    if (score > bestScore) {
      best = cell;
      bestScore = score;
    }
  }
  return best;
}

/**
 * Mirror the desktop difficulty levels without mutating the supplied board.
 * Intermediate opponents always take an immediate win. Medium notices direct
 * threats 65% of the time; hard notices 88% and chooses optimally on 60% of
 * remaining decisions. Otherwise either may choose any legal move.
 */
export function chooseMove(board, turn, difficulty, rng = Math.random) {
  if (!DIFFICULTIES.has(difficulty)) throw new RangeError(`Unknown difficulty: ${difficulty}`);
  if (outcome(board)) return null;
  if (difficulty === 'unbeatable') return bestMove(board, turn);
  const legal = board.flatMap((cell, index) => cell ? [] : [index]);
  const randomMove = () => legal[Math.floor(rng() * legal.length)];
  if (difficulty === 'easy') return randomMove();
  for (const cell of legal) {
    if (outcome(afterMove(board, cell, turn)) === turn) return cell;
  }
  const other = opposite(turn);
  for (const cell of legal) {
    if (outcome(afterMove(board, cell, other)) === other) {
      const probability = difficulty === 'medium' ? 0.65 : 0.88;
      return rng() < probability ? cell : randomMove();
    }
  }
  if (difficulty === 'hard' && rng() < 0.60) return bestMove(board, turn);
  return randomMove();
}
