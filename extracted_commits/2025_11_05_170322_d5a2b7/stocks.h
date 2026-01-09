#ifndef _STOCKS_H
#define _STOCKS_H

#include "types.h"
#include "stacks.h"

//stocks.c
int		getMinSumOfBlocksAndBlanks		(Line*,		int);
int		getMinSumOfBlocksAndBlanksPrev	(Line*,		int);
int		getLengthOfLargestBlock			(Line*);
void 	FreePuzzle						(Puzzle*);
void 	FreeStacks						(Stack**);
Stack** InitStacks						(Puzzle*);
Cell* 	PickCell						(Puzzle*,	int*,	int*);
void 	ConditionalPush					(Stack*,	Line*);
int 	getSumOfBlocks					(Line*);
int 	checkline						(Line*, 	int);
int 	checkpuzzle						(Puzzle*);
void 	LinkCellsToLines				(Puzzle*);
void 	SetupMinsAndMaxes				(Puzzle*);

#endif
