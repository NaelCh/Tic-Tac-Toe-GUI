import assert from 'node:assert/strict';
import test from 'node:test';
import { LINES, winningLine, outcome, bestMove, chooseMove } from '../engine.js';

const levels = ['easy', 'medium', 'hard', 'unbeatable'];
const empty = () => Array(9).fill('');
const other = (turn) => turn === 'X' ? 'O' : 'X';
const sequence = (...rolls) => {
  let index = 0;
  return () => rolls[Math.min(index++, rolls.length - 1)];
};

function play(board, cell, turn) {
  assert.equal(board[cell], '');
  const next = board.slice();
  next[cell] = turn;
  return next;
}

test('all eight winning lines for either symbol', () => {
  for (const symbol of ['X', 'O']) {
    for (const line of LINES) {
      const board = empty();
      for (const cell of line) board[cell] = symbol;
      assert.equal(outcome(board), symbol);
      assert.deepEqual(winningLine(board), line);
    }
  }
});

test('distinguishes ongoing games and a draw, with no terminal move', () => {
  assert.equal(outcome(empty()), null);
  assert.deepEqual(winningLine(empty()), []);
  const draw = ['X', 'O', 'X', 'X', 'O', 'O', 'O', 'X', 'X'];
  assert.equal(outcome(draw), 'draw');
  const won = ['X', 'X', 'X', 'O', 'O', '', '', '', ''];
  for (const board of [draw, won]) {
    assert.equal(bestMove(board, 'O'), null);
    for (const level of levels) assert.equal(chooseMove(board, 'O', level), null);
  }
});

test('intermediate levels take a win before defending, for either symbol', () => {
  for (const turn of ['X', 'O']) {
    const board = [turn, turn, '', other(turn), other(turn), '', '', '', ''];
    for (const level of ['medium', 'hard', 'unbeatable']) {
      assert.equal(chooseMove(board, turn, level, () => { throw new Error('No random decision needed'); }), 2);
    }
  }
});

test('medium and hard defend immediate threats when noticed', () => {
  for (const turn of ['X', 'O']) {
    const board = [other(turn), other(turn), '', '', turn, '', '', '', ''];
    for (const level of ['medium', 'hard']) {
      assert.equal(chooseMove(board, turn, level, () => 0), 2);
    }
  }
});

test('intermediate opponents can overlook a threat and lose', () => {
  for (const turn of ['X', 'O']) {
    for (const level of ['medium', 'hard']) {
      let board = [other(turn), other(turn), '', '', turn, '', '', '', ''];
      const cell = chooseMove(board, turn, level, sequence(0.99, 0.99));
      assert.equal(cell, 8);
      board = play(board, cell, turn);
      board = play(board, 2, other(turn));
      assert.equal(outcome(board), other(turn));
    }
  }
});

test('hard notices a threat medium can miss, and a lapse can still block by chance', () => {
  const board = ['X', 'X', '', '', 'O', '', '', '', ''];
  assert.equal(chooseMove(board, 'O', 'medium', sequence(0.8, 0.99)), 8);
  assert.equal(chooseMove(board, 'O', 'hard', () => 0.8), 2);
  for (const level of ['medium', 'hard']) {
    assert.equal(chooseMove(board, 'O', level, sequence(0.99, 0)), 2);
  }
});

test('easy can miss a direct threat', () => {
  const board = ['X', 'X', '', 'O', '', '', '', '', ''];
  assert.equal(chooseMove(board, 'O', 'easy', () => 0.99), 8);
});

test('hard usually avoids a fork but can still be beaten', () => {
  const board = ['X', '', '', '', 'O', '', '', '', 'X'];
  assert.ok([1, 3, 5, 7].includes(chooseMove(board, 'O', 'hard', () => 0.5)));
  for (const level of ['medium', 'hard']) {
    // With legal cells [1,2,3,5,6,7], .2 selects corner 2; X then forks at 6.
    const rng = level === 'medium' ? () => 0.2 : sequence(0.99, 0.2);
    const chosen = chooseMove(board, 'O', level, rng);
    assert.equal(chosen, 2);
    let next = play(board, chosen, 'O');
    next = play(next, 6, 'X');
    next = play(next, chooseMove(next, 'O', level, () => 0), 'O');
    const finish = next[3] ? 7 : 3;
    next = play(next, finish, 'X');
    assert.equal(outcome(next), 'X');
  }
});

test('unbeatable is deterministic and prefers center, then corners on ties', () => {
  assert.equal(bestMove(empty(), 'X'), 4);
  const board = ['X', '', '', '', '', '', '', '', ''];
  assert.equal(bestMove(board, 'O'), 4);
  assert.equal(chooseMove(board, 'O', 'unbeatable', () => { throw new Error('Must ignore randomness'); }), 4);
  assert.equal(bestMove(['', '', '', '', 'X', '', '', '', ''], 'O'), 0);
});

test('unbeatable never loses to any human sequence, as either player and starter', () => {
  let leaves = 0;
  function walk(board, turn, computer) {
    const result = outcome(board);
    if (result) {
      leaves += 1;
      assert.ok(result === computer || result === 'draw');
      return;
    }
    const cells = turn === computer ? [chooseMove(board, turn, 'unbeatable')]
      : board.flatMap((cell, index) => cell ? [] : [index]);
    for (const cell of cells) walk(play(board, cell, turn), other(turn), computer);
  }
  for (const computer of ['X', 'O']) {
    for (const starter of ['X', 'O']) walk(empty(), starter, computer);
  }
  assert.ok(leaves > 100);
});

test('all levels return legal moves without changing any reachable ongoing board', () => {
  const visited = new Set();
  let state = 12345;
  const rng = () => ((state = (Math.imul(state, 1664525) + 1013904223) >>> 0) / 4294967296);
  function walk(board, turn) {
    if (outcome(board)) return;
    const key = `${turn}:${board.join('-')}`;
    if (visited.has(key)) return;
    visited.add(key);
    const before = board.slice();
    Object.freeze(board);
    for (const level of levels) {
      const cell = chooseMove(board, turn, level, rng);
      assert.ok(Number.isInteger(cell) && cell >= 0 && cell < 9 && !board[cell]);
      assert.deepEqual(board, before);
    }
    for (let cell = 0; cell < 9; cell += 1) {
      if (!board[cell]) walk(play(board, cell, turn), other(turn));
    }
  }
  for (const starter of ['X', 'O']) walk(empty(), starter);
  assert.ok(visited.size > 8000);
});

test('invalid difficulty is rejected even on a terminal board', () => {
  for (const board of [empty(), ['X', 'X', 'X', '', '', '', '', '', '']]) {
    assert.throws(() => chooseMove(board, 'O', 'unknown'), RangeError);
  }
});
