This directory contains the full data pertaining to the Strudel model from the clustering experiments described in sections 7.2 (proptypes-matrix.txt) and 8.2 (categorization-matrix.txt) of the Strudel paper.

The files contain one line for each element that was clustered (concept+property pairs in proptypes-matrix.txt and concepts in categorization-matrix.txt). Each line reports the following information in tab-delimited fields: the target element, the "true" class of the element, the cluster the element was assigned to (an integer), the values of the element for each of the dimensions used for clustering.

The first line is a header containing the field names, including the full list of dimension labels.

For example, the first few columns (fields) of the first few lines of proptypes-matrix.txt are:

ROW     TRUECLASS       CLUSTER 's+left+n       's+right+n
banana_fruit    category        2       0       0
banana_peel     part    4       0       0
banana_skin     part    1       0       0
banana_tree     location        3       0       0
boat_engine     part    1       29      0

The last of these lines tells us that the concept-property pair boat_engine is an instance of the gold standard part relation, it was put in cluster 1 by the clustering algorithm, it has a value of 29 on the 's+left+n dimension and of 0 on the dimension labeled 's+right+n (see the main paper and the online technical report for explanations of the dimension label syntax).

The first few columns of the first few lines of categorization-matrix.txt are:

ROW     TRUECLASS       CLUSTER 's+left+n_ability-n     's+left+n_adventure-n
aeroplane       vehicle 2       0       0
apple   fruit   5       0       0
bean    vegetable       4       0       0
bear    mammal  1       0       21.2156
bicycle vehicle 7       0       0

The next-to-last line tells us that bear is a mammal it was clustered into cluster 1, and it has a value of 21.2156 on dimension 's+left+n_adventure-n.

The matrices were used as input for the CLUTO clustering toolkit, available from: http://glaros.dtc.umn.edu/gkhome/views/cluto/.


