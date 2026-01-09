CFLAGS = -Wall -pedantic -std=c99 -c
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

benchmark:
	@echo "file,duration_seconds" > benchmarks.csv
	@for f in puzzles/*.cfg; do \
	  echo "Running $$f" >&2; \
	  /usr/bin/time -f '%e' -o /tmp/nonogram_time.$$ ./nonograms "$$f"; \
	  rc=$$?; \
	  t=$$(cat /tmp/nonogram_time.$$ 2>/dev/null || echo "0"); \
	  echo "$$f,$$t" >> benchmarks.csv; \
	  echo "nonogram_benchmark{file=\"$$f\",exit=\"$$rc\"} $$t"; \
	done
