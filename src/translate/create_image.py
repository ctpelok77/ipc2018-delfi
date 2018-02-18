#! /usr/bin/env python
# -*- coding: utf-8 -*-

import normalize
import options
import os
import pddl_parser
from abstract_structure_module import AbstractStructureGraph
import sys
import timers

from PIL import Image
import numpy as np

from scipy.sparse import lil_matrix, coo_matrix, csr_matrix
import math

MAX_SIZE_EXPLICIT = 15000

def create_raw_matrix_for_image(graph, hide_equal_predicates=False, bolded=False, shrink_ratio=6):
    """Create raw 0/1 matrix, bolding by adding 1s around existing ones """
    def make_bolder(i, j, m, sz):
        if i < 0 or i >= sz or j < 0 or j >= sz:
            return
        m[i,j] = 1

    sz = 0
    vertex_indices = {}
    for vertex in graph.graph.get_vertices():
        if hide_equal_predicates and vertex in graph.graph.excluded_vertices:
            continue
        vertex_indices[vertex] = sz
        sz += 1
    ## Creating a matrix
    print("Creating matrix for a graph with %s nodes.." % sz)
    ## TODO: This seems to be memory intensive in some cases (e.g., airport:p21-airport4halfMUC-p2.pddl and onwards,
    ##            nomystery-opt11-strips:p05.pddl - p10.pddl and p15.pddl - p20.pddl,  and grounded cases: openstacks-strips and trucks-strips )
    ## The size of the graph can be quite big when either the task is (parially) grounded or there are many static predicates.
    ## The problem of static predicates can be overcome by using the option --only-functions-from-initial-state
    ## An attempt on overcoming the memory consumption was made by switching to the sparse lil_matrix. However, for some reason, this does not seem to work.

    if shrink_ratio > 1:
        sz += (shrink_ratio - (sz % shrink_ratio))

    if sz > MAX_SIZE_EXPLICIT:
        matrix_data = lil_matrix((sz, sz), dtype=int)
        print("Matrix size when created: %s" % (matrix_data.data.nbytes + matrix_data.rows.nbytes))
    else:
        matrix_data = np.zeros((sz,sz), dtype=int)
        print("Matrix size when created: %s" % matrix_data.nbytes)

    print("Matrix created, filling with values for edges..")
    if bolded:
        print("Performing bolding.")
    for edge in graph.graph.edges:
        assert type(edge) is tuple
        assert len(edge) == 2
        if edge[0] in vertex_indices and edge[1] in vertex_indices:
            i = vertex_indices[edge[0]]
            j = vertex_indices[edge[1]]
            matrix_data[i,j] = 1
            if bolded:
                ## Try to make wider
                make_bolder(i+1, j, matrix_data, sz)
                make_bolder(i-1, j, matrix_data, sz)
                make_bolder(i, j+1, matrix_data, sz)
                make_bolder(i, j-1, matrix_data, sz)

    if sz > MAX_SIZE_EXPLICIT:
        nbytes_size = matrix_data.data.nbytes + matrix_data.rows.nbytes
    else:
        nbytes_size = matrix_data.nbytes

    print("Matrix size when 1s added: %s" % nbytes_size)

    return matrix_data, sz


def print_graph_statistics(graph, hide_equal_predicates=False):
    matrix_data, sz = create_raw_matrix_for_image(graph, hide_equal_predicates, bolded=False, shrink_ratio=1)
    print("Number of graph vertices: %s" % sz)
    print("Number of graph edges: %s" % matrix_data.count_nonzero())


def shrink_matrix_raw_to_grayscale(graph, hide_equal_predicates=False, bolded=False, shrink_ratio=6):
    """ Assuming no self loops!!!
    Partitioned into squares of size 6, to shrink the graph into target image size:
    Turning binaries into numbers up to 32bit signed - [0, 2147483647 = 2^31 - 1]
    Therefore the maximal square possible is 6x6 (without the diagonal, 30 entries)
    [[0,a1,a2, ...],[b1,0,b2, ...],[c1,c2,0, c3, ...], ...] is turned into 2^0 * a1 + 2^1 * a2 + ...
    """
    def get_number_or_zero(ri, ci, m):
        if len(m) > ri and len(m) > ci:
            return str(m[ri][ci])
        return "0"

    def get_number_for_square(ri, ci, m, buff):
        str_rep = ""
        for i in range(buff):
            for j in range(buff):
                if i == j:
                    continue
                str_rep += get_number_or_zero(ri + buff - 1 - i, ci + buff - 1 - j, m)

        return int(str_rep, 2)

    assert(shrink_ratio > 0)
    assert(shrink_ratio <= 6)

    matrix_data, sz = create_raw_matrix_for_image(graph, hide_equal_predicates, bolded, shrink_ratio)

    print("Number of graph nodes: %s" % sz)
    print("Shrink ratio: %s" % shrink_ratio)
    if shrink_ratio == 1:
        return matrix_data

    shrinked_sz = int(math.ceil(float(sz)/shrink_ratio))
    n = 0
    print("Shrinking matrix to size %sx%s.." % (shrinked_sz,shrinked_sz))

    if shrinked_sz > MAX_SIZE_EXPLICIT:
        shrinked_matrix_data_test = lil_matrix((shrinked_sz, shrinked_sz), dtype=int)
        print("Shrinked matrix size when created: %s" % (shrinked_matrix_data_test.data.nbytes + shrinked_matrix_data_test.rows.nbytes))
    else:
        shrinked_matrix_data_test = np.zeros((shrinked_sz,shrinked_sz), dtype=int)
        print("Shrinked matrix size when created: %s" % shrinked_matrix_data_test.nbytes)


    for i in range(shrink_ratio):
        for j in range(shrink_ratio):
            if i == j:
                continue
            shrinked_matrix_data_test += (2**n) * matrix_data[j::shrink_ratio, i::shrink_ratio]
            n += 1
    return shrinked_matrix_data_test, shrinked_sz

def write_matrix_image_grayscale(graph, output_directory, hide_equal_predicates=False, bolded=False, shrink_ratio=6, target_size=128, write_original_size=False):
    """Write the graph into a grayscale image"""
    """If shrink_ratio of 1 is used, using raw [0, 1] values for each pixel.
        If shrink_ratio of up to 3 is used, using [0, 255] values for each pixel.
        Otherwise, a 32bit signed int is used"""
    assert os.path.exists(output_directory)
    fname_base = 'graph-gs'
    grayscale_type_opts = { 1 : '1', 2 : 'L', 3 : 'L', 4 : 'I', 5 : 'I', 6 : 'I'}
    grayscale_color_opts = { '1' : 1, 'L' : 255, 'I' : 2147483647}

    grayscale_type = grayscale_type_opts[shrink_ratio]
    grayscale_color = grayscale_color_opts[grayscale_type]
    print("Grayscale color: %s" % grayscale_color)
    nm = '%s-%s-%s.png' % (fname_base, grayscale_type, ("bolded" if bolded else "reg"))
    nm_thumbnail = '%s-%s-%s-thumbnail.png' % (fname_base, grayscale_type, ("bolded" if bolded else "reg"))
    nm_constant_size = '%s-%s-%s-cs.png' % (fname_base, grayscale_type, ("bolded" if bolded else "reg"))

    matrix_data, sz = shrink_matrix_raw_to_grayscale(graph, hide_equal_predicates, bolded, shrink_ratio)
    #print matrix_data[matrix_data.nonzero()]
    ## For grayscale_type "L", sharpen the image by 4 (there are only 6 entries used, so the maximal number is 63)
    if grayscale_type == 'L':
        matrix_data = 4 * matrix_data

    im = Image.new(grayscale_type, (sz, sz), grayscale_color)
    cx = coo_matrix(matrix_data)

    for x,y,color in zip(cx.row, cx.col, cx.data):
        #print("Pixel of color %s at (%s,%s)" % (grayscale_color - color, x, y))
        im.putpixel((x, y), grayscale_color - color)

    #matrix_data = grayscale_color - matrix_data

    #im.putdata(matrix_data.flatten() + grayscale_color)

    if write_original_size:
        print("Writing grayscale image of size %sx%s .." % (sz, sz))
        im.save(os.path.join(output_directory, nm),'png')

    size = target_size, target_size

    newimg = im.resize(size, Image.ANTIALIAS)

    print("Writing grayscale image of size %sx%s .." % size)
    newimg.save(os.path.join(output_directory, nm_constant_size), "png")

    #im.thumbnail(size, Image.ANTIALIAS)
    #im.save(nm_thumbnail, "png")


if __name__ == "__main__":
    timer = timers.Timer()

    only_object_symmetries = options.only_object_symmetries
    stabilize_initial_state = not options.do_not_stabilize_initial_state
    stabilize_goal = not options.do_not_stabilize_goal

    image_output_directory = options.image_output_directory
    use_bolding = options.bolding_abstract_structure_image
    write_original_size = options.write_abstract_structure_image_original_size
    abstract_structure_image_target_size = options.abstract_structure_image_target_size

    with timers.timing("Parsing pddl..", True):
        task = pddl_parser.open()
    with timers.timing("Normalizing task..", True):
        normalize.normalize(task)
    #print("Dumping task..")
    #task.dump()
    with timers.timing("Creating abstract structure graph..", True):
        graph = AbstractStructureGraph(task, only_object_symmetries, stabilize_initial_state, stabilize_goal)
    if options.dump_dot_graph:
        f = open('out.dot', 'w')
        graph.write_dot_graph(f, hide_equal_predicates=True)
        f.close()
    if options.write_abstract_structure_image_raw:
        with timers.timing("Writing abstract structure graph raw image..", True):
            write_matrix_image_grayscale(graph, image_output_directory, hide_equal_predicates=True, shrink_ratio=1, bolded=use_bolding, target_size=abstract_structure_image_target_size, write_original_size=write_original_size)
    if options.write_abstract_structure_image_reg:
        with timers.timing("Writing abstract structure graph grayscale 8bit image..", True):
            write_matrix_image_grayscale(graph, image_output_directory, hide_equal_predicates=True, shrink_ratio=3, bolded=use_bolding, target_size=abstract_structure_image_target_size, write_original_size=write_original_size)
    if options.write_abstract_structure_image_int:
        with timers.timing("Writing abstract structure graph grayscale 32bit image..", True):
            write_matrix_image_grayscale(graph, image_output_directory, hide_equal_predicates=True, shrink_ratio=6, bolded=use_bolding, target_size=abstract_structure_image_target_size, write_original_size=write_original_size)

    print("Done creating image! %s" % timer)

    sys.stdout.flush()

