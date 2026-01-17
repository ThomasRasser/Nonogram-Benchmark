#ifndef _SOLVER_H
#define _SOLVER_H

#include "stacks.h"
#include "types.h"

void MergeBlockPositions(Line*, int);
void ExamineBlocks(Line*, int, int, int, Stack*, int);
int solveline(Puzzle*, Stack**, Stack*, int);
void solve(Puzzle*, Stack**, Stack*, int);
void run_solver(char*);

#endif
