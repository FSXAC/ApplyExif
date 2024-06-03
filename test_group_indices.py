def factor_continuous_indices(indices):
    if not indices:
        return []

    indices.sort()
    continuous_groups = []
    current_group = [indices[0]]

    for i in range(1, len(indices)):
        if indices[i] == indices[i-1] + 1:
            current_group.append(indices[i])
        else:
            continuous_groups.append(current_group)
            current_group = [indices[i]]

    continuous_groups.append(current_group)
    return continuous_groups

# Example usage
indices1 = [1, 2, 3]
indices2 = [1, 4, 5, 7, 8, 9, 10]
print(factor_continuous_indices(indices1))  # Output: [[1, 2, 3]]
print(factor_continuous_indices(indices2))  # Output: [[1], [4, 5], [7, 8, 9, 10]]
