# Algorithm Design and Analysis

## Complexity Analysis

### Time Complexity

Time complexity measures how algorithm runtime grows with input size. Common complexities:

- O(1): Constant time
- O(log n): Logarithmic (binary search)
- O(n): Linear (array traversal)
- O(n log n): Linearithmic (merge sort)
- O(n²): Quadratic (nested loops)
- O(2ⁿ): Exponential (recursive Fibonacci)

### Space Complexity

Space complexity analyzes memory usage. Consider both auxiliary space and total space required by the algorithm.

## Sorting Algorithms

### Quick Sort

Quick sort uses divide-and-conquer strategy:
1. Choose a pivot element
2. Partition array around pivot
3. Recursively sort sub-arrays

Average time complexity: O(n log n)
Worst case: O(n²)

### Merge Sort

Merge sort divides array into halves, recursively sorts them, and merges results. Guarantees O(n log n) time but requires O(n) extra space.

## Search Algorithms

### Binary Search

Binary search works on sorted arrays by repeatedly dividing the search interval in half. Time complexity: O(log n).

```
while low <= high:
    mid = (low + high) // 2
    if array[mid] == target:
        return mid
    elif array[mid] < target:
        low = mid + 1
    else:
        high = mid - 1
```

### Depth-First Search (DFS)

DFS explores graph vertices by going deep before backtracking. Uses a stack (or recursion) for implementation.

### Breadth-First Search (BFS)

BFS explores vertices level by level using a queue. Finds shortest path in unweighted graphs.

## Dynamic Programming

Dynamic programming solves problems by breaking them into overlapping subproblems. Store solutions to avoid recomputation.

Classic examples:
- Fibonacci sequence
- Longest common subsequence
- Knapsack problem
- Matrix chain multiplication

## Greedy Algorithms

Greedy algorithms make locally optimal choices hoping to find global optimum. Examples include:
- Huffman coding
- Dijkstra's shortest path
- Kruskal's minimum spanning tree
- Activity selection problem

Greedy doesn't always give optimal solution but often provides good approximations efficiently.
