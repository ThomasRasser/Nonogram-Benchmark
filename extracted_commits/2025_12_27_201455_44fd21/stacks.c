#include "stacks.h"

#include <stdlib.h>

struct _element {
    Item* item;
    struct _element* next;
};

struct _stack {
    Item** data;
    int size;
    int capacity;
};

#define INITIAL_CAPACITY 1

Stack* CreateStack() {
    Stack* stack = (Stack*)malloc(sizeof(Stack));
    if (stack == NULL) return NULL;
    stack->capacity = INITIAL_CAPACITY;
    stack->size = 0;
    stack->data = (Item**)malloc(sizeof(Item*) * stack->capacity);
    if (stack->data == NULL) {
        free(stack);
        return NULL;
    }
    return stack;
}

void Push(Stack* stack, Item* item) {
    if (stack == NULL) return;
    if (stack->size >= stack->capacity) {
        int newcap = stack->capacity * 2;
        Item** tmp = (Item**)realloc(stack->data, sizeof(Item*) * newcap);
        if (tmp == NULL) return; /* keep old buffer if realloc fails */
        stack->data = tmp;
        stack->capacity = newcap;
    }
    stack->data[stack->size++] = item;
}

Item* Pop(Stack* stack) {
    if (stack == NULL || IsStackEmpty(stack)) return NULL;
    return stack->data[--stack->size];
}

void ClearStack(Stack* stack) {
    if (stack == NULL) return;
    free(stack->data);
    stack->capacity = INITIAL_CAPACITY;
    stack->size = 0;
    stack->data = (Item**)malloc(sizeof(Item*) * stack->capacity);
    if (stack->data == NULL) {
        stack->capacity = 0;
    }
}

int IsStackEmpty(Stack* stack) {
    return (stack == NULL || stack->size == 0);
}

int IsInStack(Stack* stack, Item* item) {
    if (stack == NULL) return 0;
    for (int i = 0; i < stack->size; ++i) {
        if (stack->data[i] == item) return 1;
    }
    return 0;
}
