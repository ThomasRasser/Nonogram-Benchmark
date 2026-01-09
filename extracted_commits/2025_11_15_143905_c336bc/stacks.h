#ifndef _STACKS_H
#define _STACKS_H

typedef void Item;
typedef struct _element Element;
typedef struct _stack Stack;

Stack* CreateStack();
void Push(Stack*, Item*);
Item* Pop(Stack*);
void ClearStack(Stack*);
int IsStackEmpty(Stack*);
int IsInStack(Stack*, Item*);

#endif
