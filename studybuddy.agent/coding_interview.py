import json
import re
import sys
import os
import subprocess
import streamlit as st


# ============================================================
# CURATED QUESTION BANK (ROBUST FALLBACK / TEMPLATES)
# ============================================================

QUESTION_BANK = {
    "Python": {
        "Easy": [
            {
                "title": "Two Sum",
                "description": "Given an array of integers `nums` and an integer `target`, return the indices of the two numbers such that they add up to `target`. Each input has exactly one solution, and you may not use the same element twice.",
                "input_format": "`nums`: List[int], `target`: int",
                "output_format": "List[int] containing the two 0-based indices",
                "constraints": "2 <= len(nums) <= 10^4\n-10^9 <= nums[i] <= 10^9\nOnly one valid pair exists.",
                "example_input": "nums = [2, 7, 11, 15], target = 9",
                "example_output": "[0, 1]",
                "language": "Python",
                "difficulty": "Easy",
                "topic": "Arrays & Hash Maps",
                "starter_code": "def solution(nums, target):\n    # Write your solution here\n    # Return [index1, index2]\n    seen = {}\n    for i, n in enumerate(nums):\n        diff = target - n\n        if diff in seen:\n            return [seen[diff], i]\n        seen[n] = i\n    return []\n",
                "hints": [
                    "A brute force check takes O(n^2) time. Can a hash map reduce this to O(n)?",
                    "For each number `n`, the required complement is `target - n`.",
                    "Store each visited element and its index in a dictionary while traversing."
                ],
                "test_cases": [
                    {"input": [[2, 7, 11, 15], 9], "expected": [0, 1]},
                    {"input": [[3, 2, 4], 6], "expected": [1, 2]},
                    {"input": [[3, 3], 6], "expected": [0, 1]}
                ],
                "followup_question": "Why is dictionary lookup average O(1) in Python, and under what conditions could it degrade to O(n)?"
            },
            {
                "title": "Valid Palindrome",
                "description": "A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward. Given a string `s`, return `True` if it is a palindrome, or `False` otherwise.",
                "input_format": "`s`: str",
                "output_format": "bool (`True` or `False`)",
                "constraints": "1 <= len(s) <= 2 * 10^5\n`s` consists only of printable ASCII characters.",
                "example_input": "s = 'A man, a plan, a canal: Panama'",
                "example_output": "True",
                "language": "Python",
                "difficulty": "Easy",
                "topic": "Strings & Two Pointers",
                "starter_code": "def solution(s):\n    # Write your solution here\n    filtered = [ch.lower() for ch in s if ch.isalnum()]\n    return filtered == filtered[::-1]\n",
                "hints": [
                    "First consider filtering out non-alphanumeric characters and normalizing case.",
                    "You can compare the cleaned string with its reverse, or use two pointers from both ends.",
                    "Two pointers meeting in the middle achieve O(1) extra space without building full reversed lists."
                ],
                "test_cases": [
                    {"input": ["A man, a plan, a canal: Panama"], "expected": True},
                    {"input": ["race a car"], "expected": False},
                    {"input": [" "], "expected": True}
                ],
                "followup_question": "What is the space complexity of `filtered == filtered[::-1]` versus an in-place two-pointer check?"
            },
            {
                "title": "Find Maximum Subarray Sum (Kadane's)",
                "description": "Given an integer array `nums`, find the subarray with the largest sum, and return its sum.",
                "input_format": "`nums`: List[int]",
                "output_format": "int (maximum sum)",
                "constraints": "1 <= len(nums) <= 10^5\n-10^4 <= nums[i] <= 10^4",
                "example_input": "nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]",
                "example_output": "6",
                "language": "Python",
                "difficulty": "Easy",
                "topic": "Dynamic Programming & Arrays",
                "starter_code": "def solution(nums):\n    # Return the maximum subarray sum\n    max_sum = nums[0]\n    current_sum = nums[0]\n    for num in nums[1:]:\n        current_sum = max(num, current_sum + num)\n        max_sum = max(max_sum, current_sum)\n    return max_sum\n",
                "hints": [
                    "At each index, you decide whether to extend the previous subarray or start fresh from the current element.",
                    "If the running sum becomes negative, continuing with it will only hurt subsequent sums.",
                    "Track both `current_max` and `global_max` in a single O(n) pass."
                ],
                "test_cases": [
                    {"input": [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], "expected": 6},
                    {"input": [[1]], "expected": 1},
                    {"input": [[5, 4, -1, 7, 8]], "expected": 23}
                ],
                "followup_question": "How would you modify your solution to return the starting and ending indices of the subarray instead of just the sum?"
            },
            {
                "title": "First Unique Character in a String",
                "description": "Given a string `s`, find the first non-repeating character in it and return its index. If it does not exist, return -1.",
                "input_format": "`s`: str",
                "output_format": "int (index or -1)",
                "constraints": "1 <= len(s) <= 10^5\n`s` consists of only lowercase English letters.",
                "example_input": "s = 'leetcode'",
                "example_output": "0",
                "language": "Python",
                "difficulty": "Easy",
                "topic": "Hash Tables & Counting",
                "starter_code": "def solution(s):\n    from collections import Counter\n    counts = Counter(s)\n    for i, ch in enumerate(s):\n        if counts[ch] == 1:\n            return i\n    return -1\n",
                "hints": [
                    "You need to count the frequency of each character in the string.",
                    "A two-pass approach: first pass counts occurrences, second pass finds the first index with count == 1.",
                    "Consider using `collections.Counter` or a dictionary."
                ],
                "test_cases": [
                    {"input": ["leetcode"], "expected": 0},
                    {"input": ["loveleetcode"], "expected": 2},
                    {"input": ["aabb"], "expected": -1}
                ],
                "followup_question": "Since the string only contains lowercase English letters, can you optimize the space bound to O(1) auxiliary space?"
            },
            {
                "title": "Merge Two Sorted Lists",
                "description": "Given two sorted integer lists `list1` and `list2`, merge them into one sorted list and return it.",
                "input_format": "`list1`: List[int], `list2`: List[int]",
                "output_format": "List[int] sorted in non-decreasing order",
                "constraints": "0 <= len(list1), len(list2) <= 50\n-100 <= elements <= 100",
                "example_input": "list1 = [1, 2, 4], list2 = [1, 3, 4]",
                "example_output": "[1, 1, 2, 3, 4, 4]",
                "language": "Python",
                "difficulty": "Easy",
                "topic": "Lists & Two Pointers",
                "starter_code": "def solution(list1, list2):\n    # Return merged sorted list\n    res = []\n    i = j = 0\n    while i < len(list1) and j < len(list2):\n        if list1[i] <= list2[j]:\n            res.append(list1[i])\n            i += 1\n        else:\n            res.append(list2[j])\n            j += 1\n    res.extend(list1[i:])\n    res.extend(list2[j:])\n    return res\n",
                "hints": [
                    "Compare elements from the front of both lists using pointers.",
                    "Append the smaller element to your result list and advance its pointer.",
                    "Don't forget to append any remaining elements once one list is exhausted."
                ],
                "test_cases": [
                    {"input": [[1, 2, 4], [1, 3, 4]], "expected": [1, 1, 2, 3, 4, 4]},
                    {"input": [[], []], "expected": []},
                    {"input": [[], [0]], "expected": [0]}
                ],
                "followup_question": "How is this merge logic used inside the Merge Sort algorithm, and what is the overall time complexity of Merge Sort?"
            }
        ],
        "Medium": [
            {
                "title": "Group Anagrams",
                "description": "Given an array of strings `strs`, group the anagrams together. You can return the answer in any order.",
                "input_format": "`strs`: List[str]",
                "output_format": "List[List[str]]",
                "constraints": "1 <= len(strs) <= 10^4\n0 <= len(strs[i]) <= 100\n`strs[i]` consists of lowercase English letters.",
                "example_input": "strs = ['eat', 'tea', 'tan', 'ate', 'nat', 'bat']",
                "example_output": "[['bat'], ['nat', 'tan'], ['ate', 'eat', 'tea']]",
                "language": "Python",
                "difficulty": "Medium",
                "topic": "Hash Maps & Strings",
                "starter_code": "def solution(strs):\n    from collections import defaultdict\n    groups = defaultdict(list)\n    for s in strs:\n        key = ''.join(sorted(s))\n        groups[key].append(s)\n    return sorted([sorted(g) for g in groups.values()])\n",
                "hints": [
                    "Anagrams have identical characters when sorted.",
                    "Use a hash map where the key is either the sorted string or a character count tuple.",
                    "Group all strings matching the key into a list."
                ],
                "test_cases": [
                    {"input": [["eat", "tea", "tan", "ate", "nat", "bat"]], "expected": [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]},
                    {"input": [[""]], "expected": [[""]]},
                    {"input": [["a"]], "expected": [["a"]]}
                ],
                "followup_question": "What is the difference in time complexity between sorting each string versus using a 26-element frequency tuple as the key?"
            },
            {
                "title": "Longest Substring Without Repeating Characters",
                "description": "Given a string `s`, find the length of the longest substring without repeating characters.",
                "input_format": "`s`: str",
                "output_format": "int (length of longest unique substring)",
                "constraints": "0 <= len(s) <= 5 * 10^4\n`s` consists of English letters, digits, symbols and spaces.",
                "example_input": "s = 'abcabcbb'",
                "example_output": "3",
                "language": "Python",
                "difficulty": "Medium",
                "topic": "Sliding Window & Hash Maps",
                "starter_code": "def solution(s):\n    char_index = {}\n    max_len = 0\n    start = 0\n    for end, ch in enumerate(s):\n        if ch in char_index and char_index[ch] >= start:\n            start = char_index[ch] + 1\n        char_index[ch] = end\n        max_len = max(max_len, end - start + 1)\n    return max_len\n",
                "hints": [
                    "Use a sliding window `[start, end]` over the string.",
                    "Maintain the most recent index where each character was seen in a hash map.",
                    "If the current character was seen at or after `start`, jump `start` to `char_index[ch] + 1`."
                ],
                "test_cases": [
                    {"input": ["abcabcbb"], "expected": 3},
                    {"input": ["bbbbb"], "expected": 1},
                    {"input": ["pwwkew"], "expected": 3}
                ],
                "followup_question": "Why does the sliding window approach achieve O(n) time complexity even though both window endpoints move?"
            },
            {
                "title": "Top K Frequent Elements",
                "description": "Given an integer array `nums` and an integer `k`, return the `k` most frequent elements. You may return the answer in any order.",
                "input_format": "`nums`: List[int], `k`: int",
                "output_format": "List[int] of size `k`",
                "constraints": "1 <= len(nums) <= 10^5\n-10^4 <= nums[i] <= 10^4\n`k` is in range [1, number of unique elements].",
                "example_input": "nums = [1, 1, 1, 2, 2, 3], k = 2",
                "example_output": "[1, 2]",
                "language": "Python",
                "difficulty": "Medium",
                "topic": "Heap / Bucket Sort",
                "starter_code": "def solution(nums, k):\n    from collections import Counter\n    counts = Counter(nums)\n    return [item[0] for item in counts.most_common(k)]\n",
                "hints": [
                    "First, count the frequencies of all numbers using a hash map.",
                    "You can keep top `k` elements using a min-heap of size `k` in O(n log k) time.",
                    "Alternatively, bucket sort by frequency gives optimal O(n) linear time."
                ],
                "test_cases": [
                    {"input": [[1, 1, 1, 2, 2, 3], 2], "expected": [1, 2]},
                    {"input": [[1], 1], "expected": [1]},
                    {"input": [[4, 1, -1, 2, -1, 2, 3], 2], "expected": [-1, 2]}
                ],
                "followup_question": "Explain how bucket sort achieves O(n) time for this problem compared to heap's O(n log k)."
            },
            {
                "title": "Product of Array Except Self",
                "description": "Given an integer array `nums`, return an array `answer` such that `answer[i]` is equal to the product of all the elements of `nums` except `nums[i]`. You must solve it in O(n) time without using the division operation.",
                "input_format": "`nums`: List[int]",
                "output_format": "List[int]",
                "constraints": "2 <= len(nums) <= 10^5\n-30 <= nums[i] <= 30\nThe product of any prefix or suffix fits in a 32-bit integer.",
                "example_input": "nums = [1, 2, 3, 4]",
                "example_output": "[24, 12, 8, 6]",
                "language": "Python",
                "difficulty": "Medium",
                "topic": "Prefix & Suffix Products",
                "starter_code": "def solution(nums):\n    n = len(nums)\n    res = [1] * n\n    prefix = 1\n    for i in range(n):\n        res[i] = prefix\n        prefix *= nums[i]\n    suffix = 1\n    for i in range(n - 1, -1, -1):\n        res[i] *= suffix\n        suffix *= nums[i]\n    return res\n",
                "hints": [
                    "For each element, its result is (product of elements to the left) * (product of elements to the right).",
                    "Compute prefix products in a forward pass.",
                    "Multiply suffix products in a backward pass."
                ],
                "test_cases": [
                    {"input": [[1, 2, 3, 4]], "expected": [24, 12, 8, 6]},
                    {"input": [[-1, 1, 0, -3, 3]], "expected": [0, 0, 9, 0, 0]}
                ],
                "followup_question": "Can this problem be solved with O(1) auxiliary space (excluding the output array)?"
            },
            {
                "title": "3Sum",
                "description": "Given an integer array `nums`, return all unique triplets `[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, and `j != k`, and `nums[i] + nums[j] + nums[k] == 0`.",
                "input_format": "`nums`: List[int]",
                "output_format": "List[List[int]]",
                "constraints": "3 <= len(nums) <= 3000\n-10^5 <= nums[i] <= 10^5",
                "example_input": "nums = [-1, 0, 1, 2, -1, -4]",
                "example_output": "[[-1, -1, 2], [-1, 0, 1]]",
                "language": "Python",
                "difficulty": "Medium",
                "topic": "Arrays & Two Pointers",
                "starter_code": "def solution(nums):\n    nums.sort()\n    res = []\n    n = len(nums)\n    for i in range(n - 2):\n        if i > 0 and nums[i] == nums[i - 1]:\n            continue\n        left, right = i + 1, n - 1\n        while left < right:\n            total = nums[i] + nums[left] + nums[right]\n            if total < 0:\n                left += 1\n            elif total > 0:\n                right -= 1\n            else:\n                res.append([nums[i], nums[left], nums[right]])\n                while left < right and nums[left] == nums[left + 1]:\n                    left += 1\n                while left < right and nums[right] == nums[right - 1]:\n                    right -= 1\n                left += 1\n                right -= 1\n    return res\n",
                "hints": [
                    "Sorting the array first makes finding pairs and skipping duplicates straightforward.",
                    "Iterate with index `i`, then solve a Two Sum problem on the remainder using two pointers.",
                    "Ensure you skip identical adjacent numbers to avoid duplicate triplets."
                ],
                "test_cases": [
                    {"input": [[-1, 0, 1, 2, -1, -4]], "expected": [[-1, -1, 2], [-1, 0, 1]]},
                    {"input": [[0, 1, 1]], "expected": []},
                    {"input": [[0, 0, 0]], "expected": [[0, 0, 0]]}
                ],
                "followup_question": "What is the time complexity of 3Sum, and can it theoretically be reduced below O(n^2)?"
            }
        ],
        "Hard": [
            {
                "title": "Trapping Rain Water",
                "description": "Given `n` non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.",
                "input_format": "`height`: List[int]",
                "output_format": "int (total trapped rain water units)",
                "constraints": "n == len(height)\n1 <= n <= 2 * 10^4\n0 <= height[i] <= 10^5",
                "example_input": "height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]",
                "example_output": "6",
                "language": "Python",
                "difficulty": "Hard",
                "topic": "Two Pointers & Dynamic Programming",
                "starter_code": "def solution(height):\n    if not height:\n        return 0\n    left, right = 0, len(height) - 1\n    left_max, right_max = height[left], height[right]\n    water = 0\n    while left < right:\n        if left_max < right_max:\n            left += 1\n            left_max = max(left_max, height[left])\n            water += left_max - height[left]\n        else:\n            right -= 1\n            right_max = max(right_max, height[right])\n            water += right_max - height[right]\n    return water\n",
                "hints": [
                    "The water trapped above bar `i` is determined by `min(max_left, max_right) - height[i]`.",
                    "You can precompute prefix max and suffix max in O(n) space.",
                    "Two pointers from left and right can solve it in O(n) time and O(1) space."
                ],
                "test_cases": [
                    {"input": [[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], "expected": 6},
                    {"input": [[4, 2, 0, 3, 2, 5]], "expected": 9}
                ],
                "followup_question": "Why is it safe to advance the pointer with the smaller boundary (`left_max` vs `right_max`) in the two-pointer approach?"
            },
            {
                "title": "Sliding Window Maximum",
                "description": "You are given an array of integers `nums`, there is a sliding window of size `k` which is moving from the very left of the array to the very right. Return the max sliding window.",
                "input_format": "`nums`: List[int], `k`: int",
                "output_format": "List[int]",
                "constraints": "1 <= len(nums) <= 10^5\n1 <= k <= len(nums)",
                "example_input": "nums = [1, 3, -1, -3, 5, 3, 6, 7], k = 3",
                "example_output": "[3, 3, 5, 5, 6, 7]",
                "language": "Python",
                "difficulty": "Hard",
                "topic": "Monotonic Queue & Deque",
                "starter_code": "def solution(nums, k):\n    from collections import deque\n    dq = deque()\n    res = []\n    for i, n in enumerate(nums):\n        while dq and dq[0] < i - k + 1:\n            dq.popleft()\n        while dq and nums[dq[-1]] < n:\n            dq.pop()\n        dq.append(i)\n        if i >= k - 1:\n            res.append(nums[dq[0]])\n    return res\n",
                "hints": [
                    "A naive max check takes O(k) per window, yielding O(n * k).",
                    "Maintain a monotonic deque of indices storing candidates in decreasing value order.",
                    "Indices that fall outside the window or are smaller than the incoming element can be removed."
                ],
                "test_cases": [
                    {"input": [[1, 3, -1, -3, 5, 3, 6, 7], 3], "expected": [3, 3, 5, 5, 6, 7]},
                    {"input": [[1], 1], "expected": [1]}
                ],
                "followup_question": "Why does each element get pushed and popped at most once in the monotonic deque, resulting in amortized O(n) time?"
            }
        ]
    },
    "SQL": {
        "Easy": [
            {
                "title": "Duplicate Emails",
                "description": "Write an SQL query to report all the duplicate emails in a table named `Person`. You can return the result in any order.",
                "input_format": "Table `Person` with columns: `id` (int), `email` (varchar)",
                "output_format": "Column `email` containing emails appearing more than once",
                "constraints": "`id` is the primary key. All emails are lowercase.",
                "example_input": "Person:\n| id | email   |\n| 1  | a@b.com |\n| 2  | c@d.com |\n| 3  | a@b.com |",
                "example_output": "| email   |\n| a@b.com |",
                "language": "SQL",
                "difficulty": "Easy",
                "topic": "GROUP BY & HAVING",
                "starter_code": "SELECT email\nFROM Person\nGROUP BY email\nHAVING COUNT(email) > 1;\n",
                "hints": [
                    "You need to group rows by email address.",
                    "Use aggregate filtering to find groups with a count greater than 1.",
                    "Remember that the `HAVING` clause filters aggregated groups, whereas `WHERE` filters rows."
                ],
                "test_cases": [
                    {"input": "standard_duplicates", "expected": "a@b.com"}
                ],
                "followup_question": "What is the difference between the `WHERE` clause and the `HAVING` clause in SQL query execution order?"
            },
            {
                "title": "Employees Earning More Than Their Managers",
                "description": "Write an SQL query to find the employees who earn more than their managers. Return the result table in any order.",
                "input_format": "Table `Employee` with columns: `id` (int), `name` (varchar), `salary` (int), `managerId` (int)",
                "output_format": "Column `Employee` with employee names",
                "constraints": "`id` is the primary key column.",
                "example_input": "Employee:\n| id | name  | salary | managerId |\n| 1  | Joe   | 70000  | 3         |\n| 2  | Henry | 80000  | 4         |\n| 3  | Sam   | 60000  | Null      |\n| 4  | Max   | 90000  | Null      |",
                "example_output": "| Employee |\n| Joe      |",
                "language": "SQL",
                "difficulty": "Easy",
                "topic": "Self Joins",
                "starter_code": "SELECT e.name AS Employee\nFROM Employee e\nJOIN Employee m ON e.managerId = m.id\nWHERE e.salary > m.salary;\n",
                "hints": [
                    "You need to compare a record with another record in the exact same table.",
                    "Use a SELF JOIN by giving the table two different aliases (e.g. `e` for employee, `m` for manager).",
                    "Join condition: `e.managerId = m.id`, filter: `e.salary > m.salary`."
                ],
                "test_cases": [
                    {"input": "manager_salaries", "expected": "Joe"}
                ],
                "followup_question": "Would an INNER JOIN or LEFT JOIN be more appropriate if an employee has no manager (`managerId IS NULL`)?"
            },
            {
                "title": "Customers Who Never Order",
                "description": "Write an SQL query to report all customers who never order anything.",
                "input_format": "Table `Customers` (id, name), Table `Orders` (id, customerId)",
                "output_format": "Column `Customers` with customer names",
                "constraints": "`id` is primary key.",
                "example_input": "Customers: (1, Joe), (2, Henry), (3, Sam), (4, Max)\nOrders: (1, 3), (2, 1)",
                "example_output": "Henry, Max",
                "language": "SQL",
                "difficulty": "Easy",
                "topic": "LEFT JOIN & NULL Checks",
                "starter_code": "SELECT c.name AS Customers\nFROM Customers c\nLEFT JOIN Orders o ON c.id = o.customerId\nWHERE o.id IS NULL;\n",
                "hints": [
                    "A LEFT JOIN keeps all rows from Customers even when there are no matching orders.",
                    "Filter for rows where the joined Order id `IS NULL`.",
                    "Alternatively, you can use `NOT IN (SELECT customerId FROM Orders)` or `NOT EXISTS`."
                ],
                "test_cases": [
                    {"input": "orders_null", "expected": "Henry, Max"}
                ],
                "followup_question": "Why can `NOT IN` behave unexpectedly when the subquery returns rows containing NULL values?"
            }
        ],
        "Medium": [
            {
                "title": "Second Highest Salary",
                "description": "Write an SQL query to report the second highest salary from the `Employee` table. If there is no second highest salary, the query should report `null`.",
                "input_format": "Table `Employee` with columns: `id` (int), `salary` (int)",
                "output_format": "Column `SecondHighestSalary` containing the salary value or null",
                "constraints": "`id` is the primary key.",
                "example_input": "Employee:\n| id | salary |\n| 1  | 100    |\n| 2  | 200    |\n| 3  | 300    |",
                "example_output": "| SecondHighestSalary |\n| 200                 |",
                "language": "SQL",
                "difficulty": "Medium",
                "topic": "Subqueries & Window Functions",
                "starter_code": "SELECT MAX(salary) AS SecondHighestSalary\nFROM Employee\nWHERE salary < (SELECT MAX(salary) FROM Employee);\n",
                "hints": [
                    "Find the maximum salary, then find the maximum salary strictly less than that maximum.",
                    "Using `MAX()` on an empty set naturally evaluates to `NULL`.",
                    "Alternatively, window functions like `DENSE_RANK()` or `LIMIT 1 OFFSET 1` can be wrapped in a subquery."
                ],
                "test_cases": [
                    {"input": "three_salaries", "expected": 200}
                ],
                "followup_question": "What is the difference between `RANK()`, `DENSE_RANK()`, and `ROW_NUMBER()` in SQL when duplicate salaries exist?"
            },
            {
                "title": "Department Highest Salary",
                "description": "Write an SQL query to find employees who have the highest salary in each of the departments.",
                "input_format": "Table `Employee` (id, name, salary, departmentId), Table `Department` (id, name)",
                "output_format": "Department, Employee, Salary",
                "constraints": "`id` is primary key.",
                "example_input": "Employee and Department tables with IT and Sales",
                "example_output": "IT: Max (90000), Sales: Henry (80000)",
                "language": "SQL",
                "difficulty": "Medium",
                "topic": "Subqueries / Window Functions",
                "starter_code": "SELECT d.name AS Department, e.name AS Employee, e.salary AS Salary\nFROM Employee e\nJOIN Department d ON e.departmentId = d.id\nWHERE (e.departmentId, e.salary) IN (\n    SELECT departmentId, MAX(salary)\n    FROM Employee\n    GROUP BY departmentId\n);\n",
                "hints": [
                    "Group by `departmentId` to calculate `MAX(salary)` for each department.",
                    "Match each employee's `(departmentId, salary)` pair against the grouped maximums.",
                    "Join with the `Department` table to retrieve department names."
                ],
                "test_cases": [
                    {"input": "dept_salaries", "expected": "Highest per dept"}
                ],
                "followup_question": "How would you rewrite this query using the `DENSE_RANK()` window function with CTE (Common Table Expression)?"
            }
        ],
        "Hard": [
            {
                "title": "Department Top Three Salaries",
                "description": "A company's executives are interested in seeing who earns the most money in each of the company's departments. A high earner in a department is an employee who has a salary in the top three unique salaries for that department. Write an SQL query to find the employees who are high earners in each of the departments.",
                "input_format": "Table `Employee` (id, name, salary, departmentId), Table `Department` (id, name)",
                "output_format": "Department, Employee, Salary (top 3 unique salaries per department)",
                "constraints": "`id` is primary key.",
                "example_input": "Multiple employees per department",
                "example_output": "High earners per department with rank <= 3",
                "language": "SQL",
                "difficulty": "Hard",
                "topic": "Window Functions & DENSE_RANK",
                "starter_code": "WITH RankedSalaries AS (\n    SELECT \n        d.name AS Department,\n        e.name AS Employee,\n        e.salary AS Salary,\n        DENSE_RANK() OVER (PARTITION BY e.departmentId ORDER BY e.salary DESC) AS rnk\n    FROM Employee e\n    JOIN Department d ON e.departmentId = d.id\n)\nSELECT Department, Employee, Salary\nFROM RankedSalaries\nWHERE rnk <= 3;\n",
                "hints": [
                    "Because top three unique salaries are required, `DENSE_RANK()` must be used instead of `RANK()`.",
                    "Partition the window by `departmentId` and order by `salary DESC`.",
                    "Filter the CTE or subquery for `rnk <= 3`."
                ],
                "test_cases": [
                    {"input": "top_three_per_dept", "expected": "Ranked <= 3"}
                ],
                "followup_question": "Why does using `RANK()` instead of `DENSE_RANK()` potentially return fewer than 3 unique salary tiers if ties exist?"
            }
        ]
    },
    "DSA": {
        "Easy": [
            {
                "title": "Valid Parentheses",
                "description": "Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid. Open brackets must be closed by the same type of brackets, and open brackets must be closed in the correct order.",
                "input_format": "`s`: str",
                "output_format": "bool (`True` or `False`)",
                "constraints": "1 <= len(s) <= 10^4\n`s` consists of parentheses only '()[]{}'.",
                "example_input": "s = '()[]{}'",
                "example_output": "True",
                "language": "Python",
                "difficulty": "Easy",
                "topic": "Stack & Data Structures",
                "starter_code": "def solution(s):\n    stack = []\n    mapping = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in mapping:\n            top = stack.pop() if stack else '#'\n            if mapping[char] != top:\n                return False\n        else:\n            stack.append(char)\n    return not stack\n",
                "hints": [
                    "A Last-In, First-Out (LIFO) stack is ideal for matching nested pairs.",
                    "Push opening brackets onto the stack. For each closing bracket, check if it matches the top element.",
                    "If the stack is empty at the end, all brackets were properly matched."
                ],
                "test_cases": [
                    {"input": ["()[]{}"], "expected": True},
                    {"input": ["(]"], "expected": False},
                    {"input": ["([])"], "expected": True}
                ],
                "followup_question": "What is the worst-case space complexity when the string consists of only open brackets like '((((('?"
            },
            {
                "title": "Binary Search",
                "description": "Given an array of integers `nums` which is sorted in ascending order, and an integer `target`, write a function to search `target` in `nums`. If `target` exists, then return its index. Otherwise, return -1. You must write an algorithm with O(log n) runtime complexity.",
                "input_format": "`nums`: List[int], `target`: int",
                "output_format": "int (index or -1)",
                "constraints": "1 <= len(nums) <= 10^4\nAll integers in `nums` are unique and sorted.",
                "example_input": "nums = [-1, 0, 3, 5, 9, 12], target = 9",
                "example_output": "4",
                "language": "Python",
                "difficulty": "Easy",
                "topic": "Binary Search & Divide and Conquer",
                "starter_code": "def solution(nums, target):\n    low, high = 0, len(nums) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if nums[mid] == target:\n            return mid\n        elif nums[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n",
                "hints": [
                    "Maintain two pointers `low` and `high`.",
                    "Calculate the midpoint and halve the search space each iteration.",
                    "If `nums[mid] < target`, search the right half; otherwise search the left half."
                ],
                "test_cases": [
                    {"input": [[-1, 0, 3, 5, 9, 12], 9], "expected": 4},
                    {"input": [[-1, 0, 3, 5, 9, 12], 2], "expected": -1}
                ],
                "followup_question": "In languages like C++ or Java, why is `mid = low + (high - low) / 2` preferred over `(low + high) / 2`?"
            }
        ],
        "Medium": [
            {
                "title": "Number of Islands",
                "description": "Given an `m x n` 2D binary grid `grid` which represents a map of '1's (land) and '0's (water), return the number of islands. An island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically.",
                "input_format": "`grid`: List[List[str]]",
                "output_format": "int (number of islands)",
                "constraints": "m == len(grid), n == len(grid[i])\n1 <= m, n <= 300\ngrid[i][j] is '0' or '1'.",
                "example_input": "grid = [\n  ['1','1','0','0','0'],\n  ['1','1','0','0','0'],\n  ['0','0','1','0','0'],\n  ['0','0','0','1','1']\n]",
                "example_output": "3",
                "language": "Python",
                "difficulty": "Medium",
                "topic": "Graphs & BFS/DFS",
                "starter_code": "def solution(grid):\n    if not grid:\n        return 0\n    rows, cols = len(grid), len(grid[0])\n    islands = 0\n    def dfs(r, c):\n        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != '1':\n            return\n        grid[r][c] = '0'\n        dfs(r + 1, c)\n        dfs(r - 1, c)\n        dfs(r, c + 1)\n        dfs(r, c - 1)\n    for r in range(rows):\n        for c in range(cols):\n            if grid[r][c] == '1':\n                islands += 1\n                dfs(r, c)\n    return islands\n",
                "hints": [
                    "Iterate through every cell in the grid.",
                    "When you encounter a '1', increment island count and initiate BFS or DFS to sink/mark the connected land.",
                    "Ensure boundary checks prevent index out of bounds."
                ],
                "test_cases": [
                    {"input": [[["1", "1", "1"], ["0", "1", "0"], ["1", "1", "1"]]], "expected": 1},
                    {"input": [[["1", "0"], ["0", "1"]]], "expected": 2}
                ],
                "followup_question": "What is the maximum recursion depth for DFS on an m x n grid, and how could BFS prevent call stack overflow?"
            }
        ],
        "Hard": [
            {
                "title": "Merge k Sorted Lists",
                "description": "You are given an array of `k` sorted integer lists. Merge all the lists into one sorted list and return it.",
                "input_format": "`lists`: List[List[int]]",
                "output_format": "List[int] sorted",
                "constraints": "k == len(lists)\n0 <= k <= 10^4\n0 <= len(lists[i]) <= 500",
                "example_input": "lists = [[1, 4, 5], [1, 3, 4], [2, 6]]",
                "example_output": "[1, 1, 2, 3, 4, 4, 5, 6]",
                "language": "Python",
                "difficulty": "Hard",
                "topic": "Priority Queue & Divide and Conquer",
                "starter_code": "def solution(lists):\n    import heapq\n    heap = []\n    for i, lst in enumerate(lists):\n        if lst:\n            heapq.heappush(heap, (lst[0], i, 0))\n    res = []\n    while heap:\n        val, list_idx, elem_idx = heapq.heappop(heap)\n        res.append(val)\n        if elem_idx + 1 < len(lists[list_idx]):\n            next_val = lists[list_idx][elem_idx + 1]\n            heapq.heappush(heap, (next_val, list_idx, elem_idx + 1))\n    return res\n",
                "hints": [
                    "A min-heap can store the current smallest element from each of the `k` lists.",
                    "Whenever you pop the minimum element, push the next element from that same list into the heap.",
                    "This achieves O(N log k) time complexity where N is the total number of elements."
                ],
                "test_cases": [
                    {"input": [[[1, 4, 5], [1, 3, 4], [2, 6]]], "expected": [1, 1, 2, 3, 4, 4, 5, 6]},
                    {"input": [[]], "expected": []}
                ],
                "followup_question": "Compare the min-heap approach with divide-and-conquer pairwise merging in terms of asymptotic time and space."
            }
        ]
    },
    "Java": {
        "Easy": [
            {
                "title": "Reverse String in Java",
                "description": "Write a Java method to reverse a character array in-place with O(1) extra memory.",
                "input_format": "`char[] s`",
                "output_format": "Reverse the array in-place or return as string",
                "constraints": "1 <= s.length <= 10^5",
                "example_input": "['h','e','l','l','o']",
                "example_output": "['o','l','l','e','h']",
                "language": "Java",
                "difficulty": "Easy",
                "topic": "Arrays & Two Pointers",
                "starter_code": "public class Solution {\n    public void reverseString(char[] s) {\n        int left = 0, right = s.length - 1;\n        while (left < right) {\n            char temp = s[left];\n            s[left] = s[right];\n            s[right] = temp;\n            left++;\n            right--;\n        }\n    }\n}\n",
                "hints": [
                    "Use two pointers: one at the start, one at the end.",
                    "Swap the characters and move towards the center.",
                    "Stop when left >= right."
                ],
                "test_cases": [
                    {"input": "['h','e','l','l','o']", "expected": "['o','l','l','e','h']"}
                ],
                "followup_question": "Why are Java `String` objects immutable, and why is `StringBuilder` preferred for repeated concatenations?"
            },
            {
                "title": "Check if Array Contains Duplicates",
                "description": "Given an integer array `nums`, return `true` if any value appears at least twice in the array, and return `false` if every element is distinct.",
                "input_format": "`int[] nums`",
                "output_format": "`boolean`",
                "constraints": "1 <= nums.length <= 10^5",
                "example_input": "nums = [1, 2, 3, 1]",
                "example_output": "true",
                "language": "Java",
                "difficulty": "Easy",
                "topic": "HashSet & Collections",
                "starter_code": "import java.util.HashSet;\n\npublic class Solution {\n    public boolean containsDuplicate(int[] nums) {\n        HashSet<Integer> set = new HashSet<>();\n        for (int num : nums) {\n            if (!set.add(num)) {\n                return true;\n            }\n        }\n        return false;\n    }\n}\n",
                "hints": [
                    "A `HashSet` in Java stores only unique elements.",
                    "`set.add(element)` returns `false` if the element was already present.",
                    "This achieves O(n) time complexity and O(n) space complexity."
                ],
                "test_cases": [
                    {"input": "[1, 2, 3, 1]", "expected": "true"}
                ],
                "followup_question": "How does `HashSet` work internally in Java, and what roles do `hashCode()` and `equals()` play?"
            }
        ],
        "Medium": [
            {
                "title": "LRU Cache Design",
                "description": "Design a data structure that follows the constraints of a Least Recently Used (LRU) cache with `get(key)` and `put(key, value)` in O(1) average time complexity.",
                "input_format": "`capacity`: int, operations sequence",
                "output_format": "Cache outputs",
                "constraints": "1 <= capacity <= 3000\nget and put operations must run in O(1) average time.",
                "example_input": "LRUCache(2); put(1, 1); put(2, 2); get(1); put(3, 3); get(2);",
                "example_output": "[null, null, null, 1, null, -1]",
                "language": "Java",
                "difficulty": "Medium",
                "topic": "Doubly Linked List & HashMap",
                "starter_code": "import java.util.HashMap;\n\nclass LRUCache {\n    // Implement doubly linked list node and hash map\n    public LRUCache(int capacity) {\n    }\n    public int get(int key) {\n        return -1;\n    }\n    public void put(int key, int value) {\n    }\n}\n",
                "hints": [
                    "A HashMap provides O(1) key lookups.",
                    "A doubly linked list allows O(1) node removal and insertion at the head (most recently used).",
                    "Java's `LinkedHashMap` can also be configured as an access-order LRU cache."
                ],
                "test_cases": [
                    {"input": "LRU basic", "expected": "O(1) operations"}
                ],
                "followup_question": "How does Java's `LinkedHashMap` provide built-in support for LRU eviction using `removeEldestEntry`?"
            }
        ],
        "Hard": [
            {
                "title": "Word Search II (Trie + Backtracking)",
                "description": "Given an `m x n` board of characters and a list of strings `words`, return all words on the board. Each word must be constructed from letters of sequentially adjacent cells.",
                "input_format": "`char[][] board`, `String[] words`",
                "output_format": "`List<String>`",
                "constraints": "m, n <= 12\nwords.length <= 3 * 10^4",
                "example_input": "board with letters, words = ['oath', 'pea', 'eat', 'rain']",
                "example_output": "['eat', 'oath']",
                "language": "Java",
                "difficulty": "Hard",
                "topic": "Trie & Backtracking",
                "starter_code": "public class Solution {\n    // Implement TrieNode and DFS backtracking\n}\n",
                "hints": [
                    "Store all dictionary words in a Prefix Tree (Trie).",
                    "Perform DFS from every cell on the board, traversing only matching Trie branches.",
                    "Prune leaves from the Trie once a word is found to optimize subsequent searches."
                ],
                "test_cases": [
                    {"input": "board words", "expected": "matched words"}
                ],
                "followup_question": "Why is a Trie significantly faster than running standard Word Search DFS independently for every word?"
            }
        ]
    }
}


# ============================================================
# HELPER: CANDIDATE SKILLS DETECTION & PERSONALIZATION
# ============================================================

def get_candidate_skills(session_state):
    """
    Extract technical skills and weak subjects identified across StudyBuddy modules.
    """
    skills = []
    
    # 1. From matched_skills
    if session_state.get("matched_skills"):
        for s in session_state["matched_skills"]:
            if s and s not in skills:
                skills.append(s)

    # 2. From skill_gap_analysis
    sg = session_state.get("skill_gap_analysis")
    if isinstance(sg, dict):
        for item in sg.get("material_skills", []):
            if item and item not in skills:
                skills.append(item)
        for item in sg.get("learned", []):
            if item and item not in skills:
                skills.append(item)

    # 3. From weak_subjects / missing_topics
    for ws in session_state.get("weak_subjects", []):
        if ws and ws not in skills:
            skills.append(ws)
    for mt in session_state.get("missing_topics", []):
        if mt and mt not in skills:
            skills.append(mt)

    # 4. From full_text keyword detection if skills list is still sparse
    full_text = (session_state.get("full_text") or "").lower()
    tech_keywords = {
        "Python": ["python", "pandas", "numpy", "flask", "django"],
        "Java": ["java", "spring", "jvm", "hibernate"],
        "SQL": ["sql", "mysql", "database", "postgres", "queries"],
        "Data Structures": ["data structure", "linked list", "binary tree", "stack", "queue", "graph", "algorithm"],
        "OOP": ["object oriented", "inheritance", "polymorphism", "encapsulation", "oop"],
        "Web Development": ["javascript", "html", "css", "api", "rest"],
    }
    for label, keywords in tech_keywords.items():
        if any(kw in full_text for kw in keywords) and label not in skills:
            skills.append(label)

    return skills


def clean_category_name(raw_type):
    """Normalize user selection e.g. '🐍 Python' -> 'Python'."""
    raw = (raw_type or "").lower()
    if "python" in raw:
        return "Python"
    if "java" in raw:
        return "Java"
    if "sql" in raw:
        return "SQL"
    if "dsa" in raw:
        return "DSA"
    return "Mixed"


def clean_difficulty_name(raw_diff):
    """Normalize difficulty selection e.g. '🟢 Easy' -> 'Easy'."""
    raw = (raw_diff or "").lower()
    if "hard" in raw or "🔴" in raw:
        return "Hard"
    if "medium" in raw or "🟡" in raw:
        return "Medium"
    return "Easy"


# ============================================================
# HELPER: LLM INVOCATION & JSON EXTRACTION
# ============================================================

def safe_extract_json(text):
    """Safely parse JSON from LLM string output with multiple fallback strategies."""
    if not text:
        return None
    cleaned = str(text).strip()
    
    # Strip markdown code fences
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()
    
    # Direct load
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Extract outermost { ... }
    match_obj = re.search(r"(\{[\s\S]*\})", cleaned)
    if match_obj:
        try:
            return json.loads(match_obj.group(1))
        except Exception:
            pass

    # Extract outermost [ ... ]
    match_arr = re.search(r"(\[[\s\S]*\])", cleaned)
    if match_arr:
        try:
            return json.loads(match_arr.group(1))
        except Exception:
            pass

    return None


def invoke_llm_safely(prompt):
    """Call Ollama LLM safely and return response text."""
    try:
        from agent import get_llm
        llm = get_llm()
        res = llm.invoke(prompt)
        if hasattr(res, "content"):
            return res.content
        return str(res)
    except Exception as e:
        return ""


# ============================================================
# QUESTION GENERATION
# ============================================================

def get_fallback_question(category, difficulty, index=0):
    """Retrieve a guaranteed, curated question from QUESTION_BANK."""
    cat = category if category in QUESTION_BANK else "Python"
    diff = difficulty if diff_in_bank(cat, difficulty) else "Easy"
    pool = QUESTION_BANK[cat][diff]
    q_data = pool[index % len(pool)]
    # Return a deep copy
    return json.loads(json.dumps(q_data))


def diff_in_bank(cat, diff):
    return cat in QUESTION_BANK and diff in QUESTION_BANK[cat] and len(QUESTION_BANK[cat][diff]) > 0


def generate_coding_question(
    interview_type="🐍 Python",
    difficulty="🟢 Easy",
    question_index=0,
    personalized_skills=None,
    retriever=None
):
    """
    Generate one structured coding question matching the student's
    interview parameters and detected academic skills.
    """
    cat = clean_category_name(interview_type)
    diff = clean_difficulty_name(difficulty)

    # In Mixed mode, select category based on detected skills and question index
    if cat == "Mixed":
        available_cats = []
        p_skills_lower = [s.lower() for s in (personalized_skills or [])]
        if any("python" in s for s in p_skills_lower):
            available_cats.append("Python")
        if any("sql" in s or "database" in s for s in p_skills_lower):
            available_cats.append("SQL")
        if any("data structure" in s or "algorithm" in s or "dsa" in s for s in p_skills_lower):
            available_cats.append("DSA")
        if any("java" in s for s in p_skills_lower):
            available_cats.append("Java")
        
        if not available_cats:
            available_cats = ["Python", "SQL", "DSA"]
        
        cat = available_cats[question_index % len(available_cats)]

    # Fetch context snippet from retriever if available
    context_snippet = ""
    if retriever:
        try:
            docs = retriever.invoke(f"{cat} coding concepts programming algorithms data structures")
            if docs:
                context_snippet = "\n".join(d.page_content for d in docs[:2])[:800]
        except Exception:
            context_snippet = ""

    skills_hint = ", ".join(personalized_skills[:5]) if personalized_skills else "general curriculum"

    prompt = f"""
You are an expert technical interviewer conducting an AI Coding Interview.
Generate Question #{question_index + 1} of 5.

Parameters:
- Category / Language: {cat}
- Difficulty Level: {diff}
- Student Detected Coursework Skills: {skills_hint}
- Academic Context: {context_snippet or 'Standard computer science curriculum'}

Create an engaging, realistic interview question.
Do NOT reveal the full solution in the problem statement.
You MUST output ONLY a valid JSON object with the following exact keys:
{{
  "title": "Short descriptive title",
  "description": "Complete problem statement",
  "input_format": "Explanation of input parameters",
  "output_format": "Explanation of return value",
  "constraints": "Time and memory bounds, input range",
  "example_input": "nums = [2, 7, 11, 15], target = 9",
  "example_output": "[0, 1]",
  "language": "{cat}",
  "difficulty": "{diff}",
  "topic": "Specific topic (e.g. Arrays, Trees, JOINs, OOP)",
  "starter_code": "def solution(...):\\n    pass\\n",
  "hints": [
    "Hint 1: Small conceptual clue without code.",
    "Hint 2: More specific algorithm or data structure clue.",
    "Hint 3: Approach guidance."
  ],
  "test_cases": [
    {{"input": [[2, 7, 11, 15], 9], "expected": [0, 1]}},
    {{"input": [[3, 2, 4], 6], "expected": [1, 2]}}
  ],
  "followup_question": "A conceptual interview follow-up question related to the solution's complexity or trade-offs."
}}

Respond ONLY with the JSON object. Do not include markdown code fences or explanatory text.
"""

    # Attempt AI generation with retry
    for attempt in range(2):
        ai_resp = invoke_llm_safely(prompt)
        parsed = safe_extract_json(ai_resp)
        if isinstance(parsed, dict) and "title" in parsed and "description" in parsed:
            # Ensure essential keys exist
            parsed.setdefault("language", cat)
            parsed.setdefault("difficulty", diff)
            parsed.setdefault("topic", cat)
            parsed.setdefault("starter_code", f"def solution(*args):\n    # Write your solution in {cat}\n    pass\n")
            if not parsed.get("hints") or not isinstance(parsed["hints"], list):
                parsed["hints"] = [
                    "Think about the most appropriate data structure for this problem.",
                    "Consider time complexity constraints when picking your approach.",
                    "Break the problem into small logical steps."
                ]
            if not parsed.get("test_cases"):
                parsed["test_cases"] = [{"input": "test_input", "expected": "test_output"}]
            if not parsed.get("followup_question"):
                parsed["followup_question"] = f"What is the time and space complexity of your {cat} solution?"
            return parsed

    # Graceful fallback to guaranteed question bank
    return get_fallback_question(cat, diff, question_index)


def generate_coding_interview(
    interview_type="🐍 Python",
    difficulty="🟢 Easy",
    total_questions=5,
    context_skills=None,
    retriever=None
):
    """Generate the full set of questions for the interview."""
    questions = []
    for i in range(total_questions):
        q = generate_coding_question(
            interview_type=interview_type,
            difficulty=difficulty,
            question_index=i,
            personalized_skills=context_skills,
            retriever=retriever
        )
        questions.append(q)
    return questions


# ============================================================
# SAFE CODE EXECUTION
# ============================================================

def run_code_safely(code, language, test_cases):
    """
    Safely execute student's code in a restricted isolated subprocess.
    If the language is non-Python, or execution encounters an issue,
    gracefully returns safe AI evaluation status.
    NEVER crashes the Streamlit process.
    """
    if not code or not code.strip():
        return {
            "status": "error",
            "passed": 0,
            "total": len(test_cases) if test_cases else 0,
            "message": "⚠️ Empty code submitted. Please write your code before running."
        }

    lang = (language or "").lower()
    
    # Only Python is executed via subprocess; SQL / Java fall back safely to AI evaluation
    if "python" not in lang:
        return {
            "status": "ai_review",
            "passed": 0,
            "total": len(test_cases) if test_cases else 0,
            "message": f"Code submitted for AI evaluation. ({language} is evaluated via AI Code Reviewer)"
        }

    # Verify test_cases validity
    if not test_cases or not isinstance(test_cases, list):
        return {
            "status": "ai_review",
            "passed": 0,
            "total": 0,
            "message": "Code submitted for AI evaluation."
        }

    # Build safe isolated test harness
    safe_script = f"""
import sys
import json

# Student submitted code
{code}

test_cases = {json.dumps(test_cases)}
passed = 0
results = []

for i, tc in enumerate(test_cases):
    try:
        inp = tc.get('input')
        exp = tc.get('expected')
        
        # Check if function 'solution' is defined
        if 'solution' in globals() and callable(globals()['solution']):
            fn = globals()['solution']
            if isinstance(inp, list):
                res = fn(*inp)
            else:
                res = fn(inp)
        else:
            # Look for any callable function defined in the code
            user_funcs = [v for k, v in globals().items() if callable(v) and not k.startswith('_') and k not in ['json', 'sys']]
            if user_funcs:
                fn = user_funcs[0]
                if isinstance(inp, list):
                    res = fn(*inp)
                else:
                    res = fn(inp)
            else:
                results.append({{'case': i+1, 'passed': False, 'error': 'No solution() function found.'}})
                continue

        # Flexible matching
        is_pass = False
        if res == exp:
            is_pass = True
        elif isinstance(res, (list, tuple)) and isinstance(exp, (list, tuple)):
            try:
                if sorted(res) == sorted(exp):
                    is_pass = True
            except Exception:
                pass

        if is_pass:
            passed += 1
            results.append({{'case': i+1, 'passed': True}})
        else:
            results.append({{'case': i+1, 'passed': False, 'expected': str(exp), 'got': str(res)}})
    except Exception as ex:
        results.append({{'case': i+1, 'passed': False, 'error': str(ex)}})

print(json.dumps({{'passed': passed, 'total': len(test_cases), 'results': results}}))
"""

    try:
        exec_result = subprocess.run(
            [sys.executable, "-c", safe_script],
            capture_output=True,
            text=True,
            timeout=3.0  # 3-second hard timeout to prevent infinite loops
        )
        
        stdout_clean = (exec_result.stdout or "").strip()
        if exec_result.returncode == 0 and stdout_clean:
            try:
                data = json.loads(stdout_clean)
                return {
                    "status": "executed",
                    "passed": data.get("passed", 0),
                    "total": data.get("total", len(test_cases)),
                    "results": data.get("results", []),
                    "message": f"Passed: {data.get('passed', 0)} / {data.get('total', len(test_cases))}"
                }
            except Exception:
                pass

        # If there was a syntax/runtime error in student code
        err_msg = exec_result.stderr.strip() or "Execution failed"
        # Extract last line of traceback for cleaner display
        short_err = err_msg.splitlines()[-1] if err_msg.splitlines() else err_msg
        return {
            "status": "executed",
            "passed": 0,
            "total": len(test_cases),
            "results": [{"case": 1, "passed": False, "error": short_err}],
            "message": f"Passed: 0 / {len(test_cases)} ({short_err})"
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "executed",
            "passed": 0,
            "total": len(test_cases),
            "results": [{"case": 1, "passed": False, "error": "Execution timed out (limit: 3 seconds). Check for infinite loops."}],
            "message": f"Passed: 0 / {len(test_cases)} (Execution Timed Out)"
        }
    except Exception as e:
        # Fallback to AI evaluation
        return {
            "status": "ai_review",
            "passed": 0,
            "total": len(test_cases),
            "message": "Code submitted for AI evaluation."
        }


# ============================================================
# AI CODE EVALUATION
# ============================================================

def evaluate_code_submission(question_data, student_code, test_results=None):
    """
    Evaluate student code against:
    - Correctness: /10
    - Logic: /10
    - Code Quality: /10
    - Efficiency: /10
    - Time Complexity
    - Space Complexity
    - Strengths
    - Weaknesses
    - Improvement Suggestions
    - Follow-up Interview Question
    """
    if not student_code or not student_code.strip():
        return {
            "correctness": 0,
            "logic": 0,
            "code_quality": 0,
            "efficiency": 0,
            "time_complexity": "N/A",
            "space_complexity": "N/A",
            "strengths": ["None (Empty solution submitted)"],
            "weaknesses": ["No code was provided for review."],
            "suggestions": ["Write a complete implementation addressing the problem."],
            "followup_question": "What is the initial algorithm you would choose to approach this problem?"
        }

    # Pass test case information to the LLM if available
    test_context = ""
    if test_results and test_results.get("status") == "executed":
        test_context = f"Test Cases Result: Passed {test_results.get('passed', 0)} of {test_results.get('total', 0)} test cases."

    prompt = f"""
You are a senior technical interviewer at a top tech company evaluating a candidate's code submission.

Problem: {question_data.get('title')}
Description: {question_data.get('description')}
Language: {question_data.get('language')}
Difficulty: {question_data.get('difficulty')}
Topic: {question_data.get('topic')}

Candidate Submitted Code:
```
{student_code}
```
{test_context}

Evaluate the code rigorously.
Provide integer scores out of 10 for:
1. correctness (0-10)
2. logic (0-10)
3. code_quality (0-10)
4. efficiency (0-10)

Also identify Time Complexity, Space Complexity, Strengths (list), Weaknesses (list), Improvement Suggestions (list), and one thoughtful Interviewer Follow-up Question tailored to the student's implementation.

Respond ONLY with a valid JSON object in this exact schema:
{{
  "correctness": 8,
  "logic": 8,
  "code_quality": 7,
  "efficiency": 8,
  "time_complexity": "O(n)",
  "space_complexity": "O(1)",
  "strengths": ["Clear loop structure", "Correct base cases"],
  "weaknesses": ["Could handle edge cases better", "Variable naming can be improved"],
  "suggestions": ["Add type hints", "Consider early returns"],
  "followup_question": "Why did you choose this approach, and how would it behave with large inputs?"
}}
"""

    resp = invoke_llm_safely(prompt)
    parsed = safe_extract_json(resp)

    if isinstance(parsed, dict) and "correctness" in parsed:
        # Sanitize score ranges 0-10
        for key in ["correctness", "logic", "code_quality", "efficiency"]:
            try:
                parsed[key] = max(0, min(10, int(parsed.get(key, 7))))
            except Exception:
                parsed[key] = 7
        
        parsed.setdefault("time_complexity", "O(n)")
        parsed.setdefault("space_complexity", "O(1)")
        parsed.setdefault("strengths", ["Solid attempt adhering to core problem constraints."])
        parsed.setdefault("weaknesses", ["Edge case coverage could be improved."])
        parsed.setdefault("suggestions", ["Refactor helper functions for clarity."])
        parsed.setdefault(
            "followup_question",
            question_data.get("followup_question") or "How would you optimize the memory footprint of this solution?"
        )
        return parsed

    # Rule-based fallback evaluation if LLM was unavailable
    passed_count = test_results.get("passed", 0) if test_results else 0
    total_count = test_results.get("total", 1) if test_results else 1
    pass_ratio = passed_count / max(1, total_count)
    
    score_base = 8 if pass_ratio == 1.0 else (6 if pass_ratio > 0 else 4)
    return {
        "correctness": score_base,
        "logic": score_base,
        "code_quality": 7,
        "efficiency": 7,
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "strengths": ["Structured solution addressing the main problem statements.", "Follows expected signature."],
        "weaknesses": ["Further edge cases or scale optimizations should be verified."],
        "suggestions": ["Add descriptive comments and assert edge cases explicitly."],
        "followup_question": question_data.get("followup_question") or "What are the asymptotic bounds of your solution?"
    }


# ============================================================
# HINT SYSTEM
# ============================================================

def generate_hint(question_data, hint_level):
    """
    Return progressive hints:
    Hint 1: Small conceptual clue.
    Hint 2: More specific algorithm clue.
    Hint 3: Approach guidance.
    Never gives the complete solution.
    """
    hints = question_data.get("hints", [])
    if not hints:
        hints = [
            "Think about the foundational data structure suitable for this problem.",
            "Consider how you can optimize lookups or iterations to reduce time complexity.",
            "Break the algorithm down: initialization, loop condition, and state updates."
        ]
    
    idx = max(0, min(len(hints) - 1, hint_level - 1))
    return hints[idx]


# ============================================================
# FOLLOW-UP EVALUATION
# ============================================================

def evaluate_followup(question_data, student_code, followup_question, student_answer):
    """Evaluate student's conceptual answer to the interviewer's follow-up question."""
    if not student_answer or not student_answer.strip():
        return {
            "score": 0,
            "feedback": "No answer was provided for the follow-up question.",
            "verdict": "Needs improvement"
        }

    prompt = f"""
You are an expert technical interviewer evaluating a student's answer to an interview follow-up question.

Coding Problem: {question_data.get('title')}
Follow-up Question: {followup_question}
Candidate's Code:
{student_code}

Candidate's Answer:
"{student_answer}"

Evaluate the candidate's understanding and answer quality.
Return a valid JSON object in this exact schema:
{{
  "score": 9,
  "verdict": "Strong / Good / Needs Improvement",
  "feedback": "2-3 sentences explaining what was good and any missing details."
}}
"""
    resp = invoke_llm_safely(prompt)
    parsed = safe_extract_json(resp)
    if isinstance(parsed, dict) and "score" in parsed:
        try:
            parsed["score"] = max(0, min(10, int(parsed["score"])))
        except Exception:
            parsed["score"] = 8
        return parsed

    # Fallback
    return {
        "score": 8,
        "verdict": "Good Explanation",
        "feedback": "You demonstrated clear understanding of the underlying algorithmic trade-offs."
    }


# ============================================================
# FINAL INTERVIEW REPORT & CONNECTIONS
# ============================================================

def display_coding_interview_report(results, skill_gap_data=None):
    """
    Render the comprehensive coding interview report:
    - Questions Completed: 5/5
    - Scores: Correctness, Logic, Code Quality, Efficiency, Final Score /100
    - Strong Areas, Weak Areas, Topics to Practice
    - Skill Gap Analyzer Connection
    - Study Plan Connection
    """
    if not results:
        st.info("No interview results recorded yet.")
        return

    num_completed = len(results)
    tot_correct = sum(r.get("correctness", 0) for r in results)
    tot_logic = sum(r.get("logic", 0) for r in results)
    tot_quality = sum(r.get("code_quality", 0) for r in results)
    tot_efficiency = sum(r.get("efficiency", 0) for r in results)

    # Scale to XX/50 for each category
    max_cat = num_completed * 10
    scale_factor = 50.0 / max(1, max_cat)
    
    cat_correct_50 = round(tot_correct * scale_factor)
    cat_logic_50 = round(tot_logic * scale_factor)
    cat_quality_50 = round(tot_quality * scale_factor)
    cat_efficiency_50 = round(tot_efficiency * scale_factor)

    # Final score out of 100
    total_pts = tot_correct + tot_logic + tot_quality + tot_efficiency
    final_score_100 = round((total_pts / max(1, num_completed * 40)) * 100)

    st.markdown("## 💻 Coding Interview Report")
    st.caption("Comprehensive technical assessment and performance breakdown")

    # Metrics row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Questions Completed", f"{num_completed}/5")
    with col2:
        st.metric("Final Interview Score", f"{final_score_100}/100")
    with col3:
        status_label = "🌟 Excellent" if final_score_100 >= 80 else ("👍 Good Readiness" if final_score_100 >= 60 else "⚠️ Needs Practice")
        st.metric("Overall Rating", status_label)

    st.divider()

    # Category Breakdown
    st.subheader("📊 Category Performance")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Correctness", f"{cat_correct_50}/50")
        st.progress(cat_correct_50 / 50.0)
    with c2:
        st.metric("Logic", f"{cat_logic_50}/50")
        st.progress(cat_logic_50 / 50.0)
    with c3:
        st.metric("Code Quality", f"{cat_quality_50}/50")
        st.progress(cat_quality_50 / 50.0)
    with c4:
        st.metric("Efficiency", f"{cat_efficiency_50}/50")
        st.progress(cat_efficiency_50 / 50.0)

    st.divider()

    # Determine strong and weak areas based on topics and results
    strong_topics = []
    weak_topics = []
    topics_to_practice = []

    for r in results:
        q_topic = r.get("topic") or "General Programming"
        avg_q_score = (r.get("correctness", 0) + r.get("logic", 0) + r.get("code_quality", 0) + r.get("efficiency", 0)) / 4.0
        if avg_q_score >= 7.5:
            if q_topic not in strong_topics:
                strong_topics.append(q_topic)
        else:
            if q_topic not in weak_topics:
                weak_topics.append(q_topic)
            if q_topic not in topics_to_practice:
                topics_to_practice.append(q_topic)

    # In case no items in either
    if not strong_topics and results:
        strong_topics.append(results[0].get("topic", "Basic Problem Solving"))
    if not weak_topics:
        topics_to_practice.append("Advanced Algorithmic Optimizations")

    col_left, col_mid, col_right = st.columns(3)
    with col_left:
        st.markdown("### ✅ Strong Areas")
        for st_top in strong_topics:
            st.success(f"• **{st_top}**")

    with col_mid:
        st.markdown("### ⚠️ Weak Areas")
        if weak_topics:
            for wk_top in weak_topics:
                st.warning(f"• **{wk_top}**")
        else:
            st.info("No critical weaknesses detected!")

    with col_right:
        st.markdown("### 📚 Topics to Practice")
        for pr_top in topics_to_practice:
            st.write(f"• **{pr_top}** (Recommended: 5 practice problems)")

    st.divider()

    # Connection with Skill Gap Analyzer
    st.subheader("🔗 Connection with Skill Gap Analyzer")
    sg = skill_gap_data or st.session_state.get("skill_gap_analysis")
    
    correlated_priorities = []
    if isinstance(sg, dict):
        role = sg.get("role", "Target Role")
        missing_or_partial = set(sg.get("missing", []) + sg.get("partial", []) + sg.get("priority", []))
        
        st.write(f"Target Role: **{role}**")
        
        # Check if weak topics overlap with skill gap
        for wk in weak_topics:
            # Match directly or by substring
            matched = False
            for sg_skill in missing_or_partial:
                if sg_skill.lower() in wk.lower() or wk.lower() in sg_skill.lower():
                    correlated_priorities.append((sg_skill, wk))
                    matched = True
            if not matched:
                correlated_priorities.append((wk, wk))
    else:
        for wk in weak_topics:
            correlated_priorities.append((wk, wk))

    if correlated_priorities:
        for priority_skill, original_topic in correlated_priorities[:4]:
            with st.container(border=True):
                st.markdown(f"🔥 **Priority Skill:** `{priority_skill}`")
                st.write(f"**Interview Result:** Weak performance detected during problem solving in `{original_topic}`.")
                st.write(f"**Recommended Action:** Practice 5 `{priority_skill}` coding problems and review core fundamentals.")
    else:
        st.success("Great job! Your coding performance aligns well with your detected skills.")

    st.divider()

    # Connection with Study Plan
    st.subheader("🎯 Connection with Study Plan")
    st.write("Add detected weak areas as targeted coding practice items to your personalized Study Plan.")

    if st.button("➕ Add Weak Topics to Study Plan", type="primary"):
        added_count = 0
        current_plan = st.session_state.get("study_plan", [])
        if not isinstance(current_plan, list):
            current_plan = []
            st.session_state.study_plan = current_plan

        existing_names = {
            (item.get("topic", "") if isinstance(item, dict) else str(item)).lower()
            for item in current_plan
        }

        topics_to_add = weak_topics if weak_topics else topics_to_practice
        for topic in topics_to_add:
            plan_name = f"{topic} (Coding Practice)"
            if plan_name.lower() not in existing_names and topic.lower() not in existing_names:
                st.session_state.study_plan.append({
                    "topic": plan_name,
                    "priority": 1,
                    "suggested_time": "2 days",
                    "reason": "Identified as a weak area in AI Coding Interview."
                })
                existing_names.add(plan_name.lower())
                added_count += 1

        if added_count > 0:
            st.success(f"✅ Added {added_count} new topic(s) to your Study Plan! Check the 🎯 Study Plan tab to view your updated schedule.")
        else:
            st.info("These topics are already present in your Study Plan.")


# ============================================================
# RETRY & STATE RESET
# ============================================================

def reset_coding_interview():
    """
    Completely reset ONLY coding interview state variables.
    Does NOT reset PDF, Dashboard, Study Plan, Progress,
    Fresher Readiness, Skill Gap Analyzer, or Jobs.
    """
    st.session_state.coding_interview_started = False
    st.session_state.coding_interview_questions = []
    st.session_state.coding_interview_current = 0
    st.session_state.coding_interview_answers = {}
    st.session_state.coding_interview_results = []
    st.session_state.coding_interview_score = 0
    st.session_state.coding_interview_completed = False
    st.session_state.coding_interview_hint_level = 0
    st.session_state.coding_interview_run_output = None
    st.session_state.coding_interview_submitted_current = False
    st.session_state.coding_interview_followup_eval = None
    st.session_state.coding_interview_followup_submitted = False


# ============================================================
# MAIN STREAMLIT UI RENDERER
# ============================================================

def render_coding_interview_page():
    """Main Streamlit page view for '💻 AI Coding Interview'."""
    st.header("💻 AI Coding Interview")
    st.caption("Personalized technical coding interview grounded in your academic coursework and skill gaps.")

    # Safe session state initialization
    init_vars = {
        "coding_interview_started": False,
        "coding_interview_type": "🐍 Python",
        "coding_interview_difficulty": "🟢 Easy",
        "coding_interview_questions": [],
        "coding_interview_current": 0,
        "coding_interview_answers": {},
        "coding_interview_results": [],
        "coding_interview_score": 0,
        "coding_interview_completed": False,
        "coding_interview_hint_level": 0,
        "coding_interview_run_output": None,
        "coding_interview_submitted_current": False,
        "coding_interview_followup_eval": None,
        "coding_interview_followup_submitted": False,
    }
    for k, v in init_vars.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Gather candidate skills
    detected_skills = get_candidate_skills(st.session_state)

    # --------------------------------------------------------
    # 1. INTERVIEW SETUP SCREEN
    # --------------------------------------------------------
    if not st.session_state.coding_interview_started:
        st.subheader("⚙️ Interview Setup")

        # Academic Context / Personalization Banner
        if detected_skills:
            st.success(
                f"🎯 **Coursework Personalization Active:** Questions will adapt to your detected skills: "
                + ", ".join(f"`{s}`" for s in detected_skills[:6])
            )
        else:
            st.info(
                "💡 **Tip:** Upload your academic PDF on the **Dashboard** to tailor coding questions directly "
                "to your syllabus, transcript grades, and identified skill gaps. You can also start an interview now!"
            )

        col1, col2, col3 = st.columns(3)
        with col1:
            interview_type = st.selectbox(
                "Interview Type",
                [
                    "🐍 Python",
                    "☕ Java",
                    "🗄️ SQL",
                    "🧠 DSA",
                    "🔀 Mixed",
                ],
                index=0,
                help="Choose the technical domain or select Mixed to combine your detected skills."
            )
        with col2:
            difficulty = st.selectbox(
                "Difficulty",
                [
                    "🟢 Easy",
                    "🟡 Medium",
                    "🔴 Hard",
                ],
                index=0,
                help="Select your desired challenge level."
            )
        with col3:
            st.metric("Number of Questions", "5 questions")

        st.write("")
        if st.button("🚀 Start Coding Interview", type="primary", use_container_width=True):
            st.session_state.coding_interview_type = interview_type
            st.session_state.coding_interview_difficulty = difficulty
            st.session_state.coding_interview_started = True
            st.session_state.coding_interview_current = 0
            st.session_state.coding_interview_questions = []
            st.session_state.coding_interview_answers = {}
            st.session_state.coding_interview_results = []
            st.session_state.coding_interview_completed = False
            st.session_state.coding_interview_hint_level = 0
            st.session_state.coding_interview_run_output = None
            st.session_state.coding_interview_submitted_current = False
            st.session_state.coding_interview_followup_eval = None
            st.session_state.coding_interview_followup_submitted = False

            # Generate first question
            with st.spinner("Generating Question 1 tailored to your background..."):
                q1 = generate_coding_question(
                    interview_type=interview_type,
                    difficulty=difficulty,
                    question_index=0,
                    personalized_skills=detected_skills,
                    retriever=st.session_state.get("retriever")
                )
                st.session_state.coding_interview_questions = [q1]
            st.rerun()
        return

    # --------------------------------------------------------
    # 2. FINAL REPORT SCREEN
    # --------------------------------------------------------
    if st.session_state.coding_interview_completed:
        display_coding_interview_report(
            st.session_state.coding_interview_results,
            st.session_state.get("skill_gap_analysis")
        )
        st.write("")
        if st.button("🔄 Take Another Interview", type="primary", use_container_width=True):
            reset_coding_interview()
            st.rerun()
        return

    # --------------------------------------------------------
    # 3. ACTIVE INTERVIEW QUESTION SCREEN
    # --------------------------------------------------------
    current_idx = st.session_state.coding_interview_current
    questions = st.session_state.coding_interview_questions

    # Ensure question exists for current index
    if current_idx >= len(questions):
        with st.spinner(f"Generating Question {current_idx + 1} of 5..."):
            next_q = generate_coding_question(
                interview_type=st.session_state.coding_interview_type,
                difficulty=st.session_state.coding_interview_difficulty,
                question_index=current_idx,
                personalized_skills=detected_skills,
                retriever=st.session_state.get("retriever")
            )
            questions.append(next_q)
            st.session_state.coding_interview_questions = questions

    curr_question = questions[current_idx]

    # Progress Bar and Header
    progress_val = (current_idx) / 5.0
    st.progress(progress_val)
    st.markdown(f"#### Question {current_idx + 1} / 5")

    # Header tags
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.caption(f"Domain: **{curr_question.get('language', 'Python')}**")
    with col_t2:
        st.caption(f"Topic: **{curr_question.get('topic', 'Algorithms')}**")
    with col_t3:
        st.caption(f"Difficulty: **{curr_question.get('difficulty', 'Easy')}**")

    # Problem Statement Container
    with st.container(border=True):
        st.markdown(f"### {curr_question.get('title', 'Coding Challenge')}")
        st.write(curr_question.get("description", ""))

        tab_ex, tab_fmt, tab_con = st.tabs(["💡 Example", "📋 Formats", "⚠️ Constraints"])
        with tab_ex:
            st.markdown(f"**Input:** `{curr_question.get('example_input', 'N/A')}`")
            st.markdown(f"**Output:** `{curr_question.get('example_output', 'N/A')}`")
        with tab_fmt:
            st.markdown(f"**Input Format:** {curr_question.get('input_format', 'N/A')}")
            st.markdown(f"**Output Format:** {curr_question.get('output_format', 'N/A')}")
        with tab_con:
            st.markdown(f"{curr_question.get('constraints', 'Standard interview constraints apply.')}")

    # Code Editor
    st.markdown(f"##### 💻 Code Editor ({curr_question.get('language', 'Python')})")
    editor_key = f"code_input_{current_idx}"
    default_code = st.session_state.coding_interview_answers.get(
        current_idx,
        curr_question.get("starter_code", "# Write your solution here\n")
    )

    code_entered = st.text_area(
        "Write your code below:",
        value=default_code,
        height=260,
        key=editor_key,
        help="Write your solution function. Ensure correct function arguments and return types."
    )
    st.session_state.coding_interview_answers[current_idx] = code_entered

    # Action Buttons: Run Code, Get Hint, Submit Solution
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])

    with btn_col1:
        if st.button("▶️ Run Code", use_container_width=True):
            if not code_entered.strip():
                st.warning("⚠️ Please write your code before running.")
            else:
                with st.spinner("Executing against test cases..."):
                    exec_res = run_code_safely(
                        code_entered,
                        curr_question.get("language", "Python"),
                        curr_question.get("test_cases", [])
                    )
                    st.session_state.coding_interview_run_output = exec_res

    with btn_col2:
        if st.button("💡 Get Hint", use_container_width=True):
            st.session_state.coding_interview_hint_level += 1

    with btn_col3:
        if st.button("➡️ Submit Solution", type="primary", use_container_width=True):
            if not code_entered.strip():
                st.warning("⚠️ Cannot submit an empty solution. Please implement your code first.")
            else:
                with st.spinner("Submitting and evaluating your code with AI..."):
                    exec_res = run_code_safely(
                        code_entered,
                        curr_question.get("language", "Python"),
                        curr_question.get("test_cases", [])
                    )
                    st.session_state.coding_interview_run_output = exec_res

                    eval_res = evaluate_code_submission(
                        curr_question,
                        code_entered,
                        exec_res
                    )
                    eval_res["topic"] = curr_question.get("topic", "Programming")
                    eval_res["question_title"] = curr_question.get("title", f"Question {current_idx + 1}")

                    # Store result
                    results = st.session_state.coding_interview_results
                    if current_idx < len(results):
                        results[current_idx] = eval_res
                    else:
                        results.append(eval_res)
                    st.session_state.coding_interview_results = results
                    st.session_state.coding_interview_submitted_current = True
                    st.session_state.coding_interview_followup_eval = None
                    st.session_state.coding_interview_followup_submitted = False
                st.rerun()

    # Hint Display Container
    hint_lvl = st.session_state.coding_interview_hint_level
    if hint_lvl > 0:
        with st.container(border=True):
            st.markdown(f"#### 💡 Hints (Level {min(hint_lvl, 3)} of 3)")
            for h_step in range(1, min(hint_lvl, 3) + 1):
                hint_text = generate_hint(curr_question, h_step)
                if h_step == 1:
                    st.info(f"**Hint 1 (Concept):** {hint_text}")
                elif h_step == 2:
                    st.warning(f"**Hint 2 (Algorithm):** {hint_text}")
                else:
                    st.success(f"**Hint 3 (Approach):** {hint_text}")
            if hint_lvl > 3:
                st.caption("All available hints have been revealed. Give it your best shot!")

    # Test Run Output Container
    run_out = st.session_state.coding_interview_run_output
    if run_out:
        with st.container(border=True):
            if run_out.get("status") == "executed":
                passed = run_out.get("passed", 0)
                total = run_out.get("total", 0)
                if passed == total and total > 0:
                    st.success(f"✅ **Passed:** {passed} / {total} test cases")
                else:
                    st.warning(f"⚠️ **Passed:** {passed} / {total} test cases")
                
                # Show individual case details
                for res_item in run_out.get("results", []):
                    c_num = res_item.get("case", 1)
                    if res_item.get("passed"):
                        st.caption(f"• Case {c_num}: Passed ✅")
                    elif "error" in res_item:
                        st.caption(f"• Case {c_num}: Failed ❌ ({res_item['error']})")
                    else:
                        st.caption(f"• Case {c_num}: Failed ❌ (Expected: `{res_item.get('expected')}`, Got: `{res_item.get('got')}`)")
            else:
                st.info(f"ℹ️ {run_out.get('message', 'Code submitted for AI evaluation.')}")

    # Submission & Evaluation Container
    if st.session_state.coding_interview_submitted_current:
        results = st.session_state.coding_interview_results
        if current_idx < len(results):
            eval_data = results[current_idx]

            with st.container(border=True):
                st.markdown("### 📝 AI Code Evaluation")

                # Metrics row
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Correctness", f"{eval_data.get('correctness', 0)}/10")
                with m2:
                    st.metric("Logic", f"{eval_data.get('logic', 0)}/10")
                with m3:
                    st.metric("Code Quality", f"{eval_data.get('code_quality', 0)}/10")
                with m4:
                    st.metric("Efficiency", f"{eval_data.get('efficiency', 0)}/10")

                # Complexity badges
                c_col1, c_col2 = st.columns(2)
                with c_col1:
                    st.info(f"⏱️ **Time Complexity:** `{eval_data.get('time_complexity', 'O(n)')}`")
                with c_col2:
                    st.info(f"💾 **Space Complexity:** `{eval_data.get('space_complexity', 'O(1)')}`")

                # Strengths, Weaknesses, Suggestions
                s_col1, s_col2 = st.columns(2)
                with s_col1:
                    st.markdown("##### ✅ Strengths")
                    for s_item in eval_data.get("strengths", []):
                        st.write(f"• {s_item}")
                with s_col2:
                    st.markdown("##### ⚠️ Areas for Improvement")
                    for w_item in eval_data.get("weaknesses", []):
                        st.write(f"• {w_item}")

                if eval_data.get("suggestions"):
                    st.markdown("##### 💡 Suggestions")
                    for sug in eval_data.get("suggestions", []):
                        st.write(f"• {sug}")

                st.divider()

                # Follow-Up Interview Question
                st.markdown("### 🎤 Interviewer Follow-Up")
                followup_q = eval_data.get("followup_question") or curr_question.get("followup_question", "Explain the time complexity of your approach.")
                st.markdown(f"**Interviewer:** *\"{followup_q}\"*")

                followup_ans = st.text_area(
                    "Your response to the interviewer:",
                    value="",
                    key=f"followup_input_{current_idx}",
                    height=100,
                    placeholder="Explain your thought process, data structures, or time complexity trade-offs here..."
                )

                if st.button("💬 Submit Follow-up Answer", key=f"btn_followup_{current_idx}"):
                    if not followup_ans.strip():
                        st.warning("Please type your response before submitting.")
                    else:
                        with st.spinner("Evaluating your conceptual response..."):
                            f_eval = evaluate_followup(
                                curr_question,
                                code_entered,
                                followup_q,
                                followup_ans
                            )
                            st.session_state.coding_interview_followup_eval = f_eval
                            st.session_state.coding_interview_followup_submitted = True

                if st.session_state.coding_interview_followup_submitted and st.session_state.coding_interview_followup_eval:
                    f_res = st.session_state.coding_interview_followup_eval
                    with st.container(border=True):
                        st.markdown(f"**Interviewer Rating:** `{f_res.get('score', 8)}/10` — **{f_res.get('verdict', 'Good')}**")
                        st.write(f_res.get("feedback", ""))

                st.divider()

                # Next Question or Finish Button
                if current_idx < 4:
                    if st.button(f"Next Question ({current_idx + 2}/5) ➡️", type="primary", use_container_width=True):
                        st.session_state.coding_interview_current += 1
                        st.session_state.coding_interview_hint_level = 0
                        st.session_state.coding_interview_run_output = None
                        st.session_state.coding_interview_submitted_current = False
                        st.session_state.coding_interview_followup_eval = None
                        st.session_state.coding_interview_followup_submitted = False
                        st.rerun()
                else:
                    if st.button("🏁 View Final Interview Report", type="primary", use_container_width=True):
                        st.session_state.coding_interview_completed = True
                        st.rerun()
