"""
quick_sort.py

A simple Quick Sort implementation in Python.
Provides both an in-place quicksort (using Lomuto partition) and a functional
version that returns a new sorted list. Includes a small demo when run as __main__.
"""
from typing import List, Any
import random


def quick_sort_inplace(arr: List[Any], low: int = 0, high: int = None) -> None:
    """Sort arr[low:high+1] in place using Quick Sort (Lomuto partition).

    Time complexity (avg): O(n log n)
    Worst case: O(n^2) (randomized pivot mitigates this)
    """
    if high is None:
        high = len(arr) - 1
    if low < high:
        pivot_index = _partition(arr, low, high)
        quick_sort_inplace(arr, low, pivot_index - 1)
        quick_sort_inplace(arr, pivot_index + 1, high)


def _partition(arr: List[Any], low: int, high: int) -> int:
    """Lomuto partition scheme with randomized pivot."""
    # Choose a random pivot and move it to the end
    pivot_idx = random.randint(low, high)
    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def quick_sort(arr: List[Any]) -> List[Any]:
    """Functional Quick Sort: returns a new sorted list (not in-place).
    Simple and clear, but uses extra memory.
    """
    if len(arr) <= 1:
        return arr[:]
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)


if __name__ == "__main__":
    data = [3, 6, 8, 10, 1, 2, 1]
    print("Original:", data)

    # functional
    sorted_data = quick_sort(data)
    print("Sorted (functional):", sorted_data)

    # in-place
    data2 = data[:]  # copy
    quick_sort_inplace(data2)
    print("Sorted (in-place):", data2)
