#ifndef _SOLVERIO_H
#define _SOLVERIO_H

#include "types.h"

void 	ExportSolution		(Puzzle*,	char*);
void 	PrintSolution		(Puzzle*);
void 	getDimension		(Puzzle*, 	FILE*,	int);
void 	readBlockLenghts	(Puzzle*, 	FILE*,	int);
void 	errorout			(char*	, 	char*);
void 	checkblankln		(FILE*);
Puzzle*	getPuzzle			(char*);

#endif
