#include "merge_tree.h"

#include "../utils/logging.h"
#include "../utils/rng.h"
#include "../utils/system.h"

#include <cassert>
#include <iostream>

using namespace std;

namespace merge_and_shrink {
const int UNINITIALIZED = -1;

MergeTreeNode::MergeTreeNode(int ts_index)
    : parent(nullptr),
      left_child(nullptr),
      right_child(nullptr),
      ts_index(ts_index) {
}

MergeTreeNode::MergeTreeNode(
    MergeTreeNode *left_child,
    MergeTreeNode *right_child)
    : parent(nullptr),
      left_child(left_child),
      right_child(right_child),
      ts_index(UNINITIALIZED) {
    left_child->parent = this;
    right_child->parent = this;
}

MergeTreeNode::MergeTreeNode(string tree_string)
    : left_child(nullptr),
      right_child(nullptr),
      ts_index(-1) {
    assert(!tree_string.empty());
//        cout << "building tree for string " << tree_string << endl;
    char &c = tree_string[0];
    if (c == 'y') {
        ABORT("ill-specified string");
    } else if (c == 'x') {
        assert(tree_string.size() > 5); // need to have at least two subtrees
        int parentheses_counter = 1;
        string::size_type index = 1;
        while (parentheses_counter != 0) {
            if (tree_string[index] == 'x') {
                ++parentheses_counter;
            } else if (tree_string[index] == 'y') {
                --parentheses_counter;
            }
            ++index;
        }
        string left_sub_tree_string = tree_string.substr(1, index - 2);
        left_child = new MergeTreeNode(left_sub_tree_string);

        assert(tree_string[index] == 'x');
        parentheses_counter = 1;
        ++index;
        int right_index = index;
        while (parentheses_counter != 0) {
            if (tree_string[index] == 'x') {
                ++parentheses_counter;
            } else if (tree_string[index] == 'y') {
                --parentheses_counter;
            }
            ++index;
        }
        assert(index == tree_string.size());
        string right_sub_tree_string = tree_string.substr(right_index,
                                                          index - right_index - 1);
        right_child = new MergeTreeNode(right_sub_tree_string);
    } else {
        string to_be_index = tree_string.substr(0, tree_string.size() - 2);
//            cout << "to be index: " << to_be_index << endl;
        ts_index = stoi(to_be_index);
    }
}

MergeTreeNode::~MergeTreeNode() {
    delete left_child;
    delete right_child;
    left_child = nullptr;
    right_child = nullptr;
}

MergeTreeNode *MergeTreeNode::get_left_most_sibling() {
    if (has_two_leaf_children()) {
        return this;
    }
    assert(left_child && right_child);

    if (!left_child->is_leaf()) {
        return left_child->get_left_most_sibling();
    }

    assert(!right_child->is_leaf());
    return right_child->get_left_most_sibling();
}

pair<int, int> MergeTreeNode::erase_children_and_set_index(int new_index) {
    assert(has_two_leaf_children());
    int left_child_index = left_child->ts_index;
    int right_child_index = right_child->ts_index;
    assert(left_child_index != UNINITIALIZED);
    assert(right_child_index != UNINITIALIZED);
    delete left_child;
    delete right_child;
    left_child = nullptr;
    right_child = nullptr;
    assert(ts_index == UNINITIALIZED);
    ts_index = new_index;
    return make_pair(left_child_index, right_child_index);
}

MergeTreeNode *MergeTreeNode::get_parent_of_ts_index(int index) {
    if (left_child && left_child->is_leaf() && left_child->ts_index == index) {
        return this;
    }

    if (right_child && right_child->is_leaf() && right_child->ts_index == index) {
        return this;
    }

    MergeTreeNode *parent = nullptr;
    if (left_child) {
        parent = left_child->get_parent_of_ts_index(index);
    }
    if (parent) {
        return parent;
    }

    if (right_child) {
        parent = right_child->get_parent_of_ts_index(index);
    }
    return parent;
}

int MergeTreeNode::compute_num_internal_nodes() const {
    if (is_leaf()) {
        return 0;
    } else {
        int number_of_internal_nodes = 1; // count the node itself
        if (left_child) {
            number_of_internal_nodes += left_child->compute_num_internal_nodes();
        }
        if (right_child) {
            number_of_internal_nodes += right_child->compute_num_internal_nodes();
        }
        return number_of_internal_nodes;
    }
}

void MergeTreeNode::inorder(int offset, int current_indentation) const {
    if (right_child) {
        right_child->inorder(offset, current_indentation + offset);
    }
    for (int i = 0; i < current_indentation; ++i) {
        cout << " ";
    }
    cout << ts_index << endl;
    if (left_child) {
        left_child->inorder(offset, current_indentation + offset);
    }
}

MergeTree::MergeTree(
    MergeTreeNode *root,
    shared_ptr<utils::RandomNumberGenerator> rng,
    UpdateOption update_option)
    : root(root), rng(rng), update_option(update_option) {
}

MergeTree::~MergeTree() {
    delete root;
    root = nullptr;
}

pair<int, int> MergeTree::get_next_merge(int new_index) {
    MergeTreeNode *next_merge = root->get_left_most_sibling();
    return next_merge->erase_children_and_set_index(new_index);
}

void MergeTree::update(pair<int, int> merge, int new_index) {
    int ts_index1 = merge.first;
    int ts_index2 = merge.second;
    assert(root->ts_index != ts_index1 && root->ts_index != ts_index2);
    MergeTreeNode *first_parent = root->get_parent_of_ts_index(ts_index1);
    MergeTreeNode *second_parent = root->get_parent_of_ts_index(ts_index2);

    if (first_parent == second_parent) { // given merge already in the tree
        first_parent->erase_children_and_set_index(new_index);
    } else {
//        inorder_traversal(4);
//        cout << "updating: merge = " << merge << ", new index = " << new_index << endl;
        MergeTreeNode *surviving_node = nullptr;
        MergeTreeNode *to_be_removed_node = nullptr;
        if (update_option == UpdateOption::USE_FIRST) {
            surviving_node = first_parent;
            to_be_removed_node = second_parent;
        } else if (update_option == UpdateOption::USE_SECOND) {
            surviving_node = second_parent;
            to_be_removed_node = first_parent;
        } else if (update_option == UpdateOption::USE_RANDOM) {
            int random = (*rng)(2);
            surviving_node = (random == 0 ? first_parent : second_parent);
            to_be_removed_node = (random == 0 ? second_parent : first_parent);
        } else if (update_option == UpdateOption::USE_GREATER_INDEX) {
            if (ts_index1 > ts_index2) {
                surviving_node = first_parent;
                to_be_removed_node = second_parent;
            } else {
                surviving_node = second_parent;
                to_be_removed_node = first_parent;
            }
        } else if (update_option == UpdateOption::USE_SMALLER_INDEX) {
            if (ts_index1 < ts_index2) {
                surviving_node = first_parent;
                to_be_removed_node = second_parent;
            } else {
                surviving_node = second_parent;
                to_be_removed_node = first_parent;
            }
        } else {
            ABORT("Unknown merge tree update option");
        }

        // Update the leaf node corresponding to one of the indices to
        // correspond to the merged index.
        MergeTreeNode *surviving_leaf = nullptr;
        if (surviving_node->left_child->ts_index == ts_index1 ||
            surviving_node->left_child->ts_index == ts_index2) {
            surviving_leaf = surviving_node->left_child;
        } else {
            assert(surviving_node->right_child->ts_index == ts_index1 ||
                surviving_node->right_child->ts_index == ts_index2);
            surviving_leaf = surviving_node->right_child;
        }
        surviving_leaf->ts_index = new_index;

        // Remove all links to to_be_removed_node and store pointers to the
        // relevant children and its parent.
        MergeTreeNode *to_be_removed_nodes_parent = to_be_removed_node->parent;
        if (to_be_removed_nodes_parent) {
            // to_be_removed_nodes_parent can be nullptr if to_be_removed_node
            // is the root node
            if (to_be_removed_nodes_parent->left_child == to_be_removed_node) {
                to_be_removed_nodes_parent->left_child = nullptr;
            } else {
                assert(to_be_removed_nodes_parent->right_child == to_be_removed_node);
                to_be_removed_nodes_parent->right_child = nullptr;
            }
        }
        MergeTreeNode *to_be_removed_nodes_good_child = nullptr;
        if (to_be_removed_node->left_child->ts_index == ts_index1 ||
            to_be_removed_node->left_child->ts_index == ts_index2) {
            to_be_removed_nodes_good_child = to_be_removed_node->right_child;
            // set the "good" child to null so that deleting to_be_removed_node
            // does not delete the good child.
            to_be_removed_node->right_child = nullptr;
        } else {
            assert(to_be_removed_node->right_child->ts_index == ts_index1 ||
                   to_be_removed_node->right_child->ts_index == ts_index2);
            to_be_removed_nodes_good_child = to_be_removed_node->left_child;
            // set the "good" child to null so that deleting to_be_removed_node
            // does not delete the good child.
            to_be_removed_node->left_child = nullptr;
        }

        if (to_be_removed_node == root) {
            root = to_be_removed_nodes_good_child;
        }

        // delete the node (this also deletes its bad child, but not the good one)
        delete to_be_removed_node;
        to_be_removed_node = nullptr;

        // update pointers of the good child and the removed node's parent to
        // point to each other.
        to_be_removed_nodes_good_child->parent = to_be_removed_nodes_parent;
        if (to_be_removed_nodes_parent) {
            // to_be_removed_nodes_parent can be nullptr if to_be_removed_node
            // was the root node
            if (!to_be_removed_nodes_parent->left_child) {
                to_be_removed_nodes_parent->left_child = to_be_removed_nodes_good_child;
            } else {
                assert(!to_be_removed_nodes_parent->right_child);
                to_be_removed_nodes_parent->right_child = to_be_removed_nodes_good_child;
            }
        }

//        cout << "after update" << endl;
//        inorder_traversal(4);
    }
}

void MergeTree::inorder_traversal(int indentation_offset) const {
    cout << "Merge tree, read from left to right (90° rotated tree): "
         << endl;
    return root->inorder(indentation_offset, 0);
}
}
