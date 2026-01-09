#ifndef _SOLVER_H
#define _SOLVER_H

#include "stacks.h"
#include "types.h"

Line* MergeBlockPositions(Line*, int, int);
void ExamineBlocks(Line*, int, int, int, Stack*, int);
int solveline(Puzzle*, Stack**, Stack*, int);
void solve(Puzzle*, Stack**, Stack*, int);
void run_solver(char*);

#endif
