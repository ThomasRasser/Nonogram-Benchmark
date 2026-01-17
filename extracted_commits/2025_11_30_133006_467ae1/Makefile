CFLAGS = -Wall -pedantic -std=c99 -c -O2 -flto=auto
CC = gcc

solver: stacks.o solver.o solverio.o stocks.o presolver.o
	$(CC) -o nonograms solver.o stacks.o solverio.o stocks.o presolver.o

solver.o: solver.c solver.h stacks.h
	$(CC) $(CFLAGS) solver.c

presolver.o: presolver.c solver.h
	$(CC) $(CFLAGS) presolver.c

solverio.o: solverio.c solver.h stacks.h
	$(CC) $(CFLAGS) solverio.c

stacks.o: stacks.c stacks.h
	$(CC) $(CFLAGS) stacks.c
	
stocks.o: stocks.c solver.h
	$(CC) $(CFLAGS) stocks.c

clean:
	rm -f *.o *~

clean-solutions:
	rm puzzles/*.sol

benchmark:
	./nonograms puzzles/p6.cfg > temp.sol || { echo "ERROR: nonograms execution failed" >&2; rm -f temp.sol; exit 1; }
	diff -q puzzles/p6.sol temp.sol >/dev/null || { echo "ERROR: output differs from puzzles/p6.sol" >&2; rm -f temp.sol; exit 1; }
	/usr/bin/time ./nonograms puzzles/p6.cfg -b > /dev/null
