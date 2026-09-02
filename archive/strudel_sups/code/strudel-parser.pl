#!/usr/bin/perl -w

use strict "vars";
use Getopt::Std;

my $usage;
{
$usage = <<"_USAGE_";

This script takes as input a "corpus stream" in format:

word pos lemma
word pos lemma
...

and it extracts tuples in format:

concept potential-property potential-pattern

The concept is any lemma with pos-tag containing the CONCEPT string.

A property (also in lemma format) must have pos JJ.*, NN.* or VV.*,
and its pos (in format -j, -n and -v) is suffixed to it in the output.

The pattern is in format:

string+conceptposition+conceptpos+propertypos

The string part contains a string of minimally 0 and maximally m
elements (where m can be specified with option -m, and it is 5 by
default). The elements in this part are delimited by _ (when property
and concept are adjacent, the middle part is simply _). The
(non-empty) elements of patterns are triplets of (lower-cased) inflected
form, pos and lemma, delimited by /.

The conceptposition part is "left" if the concept occurs before the
property, "right" if the concept occurs after the property.

The conceptpos part gives the full pos of the concept, minus the
CONCEPT string (essentially, distinguishing singular and plural
nouns).

Similarly, the propertypos is the full pos of the property.

Different constraints that filter out implausible patterns are applied
depending on the pos of the candidate property. Please take a look
directly at the code for the rules applying in the current version
(unfortunately, they are hard-coded, and I am not documenting them
here since I expect them to change frequently, making this blurb
obsolete and misleading).

A list of "keep nouns" can be passed with option -n: these should be
lower-cased, inflected nouns (i.e., singular/plural distinction
matters) that will be considered legitimate parts of patterns
conjoining nominal concepts with nominal properties (they should be
relational nouns and parts of multi-word-preposition-like-thingies,
such as "variety", "front", etc.)

Similarly, lists of "keep verbs" (-v), "keep adjectives" (-j) and
"keep adverbs" (-r) can be passed to the script. Notice however some
important differences: first, these are lemmas, not inflected forms;
second, their function is to determine whether the patterns should
contain the corresponding inflected forms, or simply the tags. In
other words, if a verb, adjective or adverb is in keep list, any
pattern containing it will preserve the verb/adjective/adverb in its
inflected form.

The user can also pass a list of "stop words", together with their pos
(that should be simply n, j or v). These are words that will not be
treated as potential properties (for example, we probably do not want
things like get, do and more among the extracted properties, although
they match our target potential property pos patterns). Notice that
keep and stop words are not mutually exclusive: a word can be a keep
word (meaning that it will be printed "as is" in the patterns) and a
stop word (meaning that it will not be considered as a potential
property). If a word in the stop word is a potential concept, it will
be treated as such (i.e., if, say, the corpus has a word "thing
NNCONCEPT", and "thing" is in the stop word list, thing will not be
treated as a potential property of other concepts, but it will be one
of the explored concepts).

NB1: The current version of the script assumes the tagset of the
English TreeTagger (plus the NNCONCEPT and NNSCONCEPT tags). It would
be better to let the user pass the simplification rules dynamically.

NB2: NB: the script only prints the extracted patterns, it does not count
them (I expect that that will be done via something like "sort | uniq
-c")

The following parameters/options can be specified:

-h: print this documentation and exit

-m: maximum number of items that can occur between the target elements
 in a potential pattern (default: 5)

-n: list of inflected nouns that will be kept as part of patterns
 connecting two other nouns

-v: list of verb lemmas that will be kept as part of pattern (in
 inflected form) whenever it is appropriate to keep verbs

-j: list of adjective lemmas that will be kept as part of pattern
 whenever it is appropriate to keep adjectives

-r: list of adverb lemmas that will be kept as part of pattern
 whenever it is appropriate to keep adverbs

-s: list of stop words in format lemma pos (where pos is n, j or v),
 that will not be considered as potential properties

Usage examples:

strudel-parser.pl -h | more

cwb-decode -C ACORPUS -P word -P pos -P lemma |\
strudel-parser.pl - > tuples

cwb-decode -C ACORPUS -P word -P pos -P lemma |\
strudel-parser.pl - | sort | uniq -c > tuple.counts

cwb-decode -C ACORPUS -P lemma -P pos -P lemma > corpus

strudel-parser.pl corpus |\
sort | uniq -c > tuple.counts

strudel-parser.pl -m 3 corpus |\
sort | uniq -c > tuple.counts

strudel-parser.pl -n keep.nouns corpus |\
sort | uniq -c > tuple.counts

strudel-parser.pl -n keep.nouns -v keep.verbs corpus |\
sort | uniq -c > tuple.counts

strudel-parser.pl -n keep.nouns -s stop.words corpus |\ 
sort | uniq -c > tuple.counts


Copyright 2007, Marco Baroni

This program is free software. You may copy or redistribute it under
the same terms as Perl itself.

_USAGE_
}
{
    my $blah = 1;
# this useless block is here because here document confuses
# emacs
}

##################### initializing parameters #####################

my %opts = ();

getopts('hm:n:j:v:r:s:',\%opts);

if ($opts{h}) {
    print $usage;
    exit;
}

# maximum distance between targets as specified by user
# or 5 by default
my $max_dist;
if (!($max_dist = $opts{m})) {
    $max_dist = 5;
}

# we will keep 4 arrays that could maximally contain one full pattern
# on the left of a target and one full pattern on the right of the
# pattern, thus:
#
# pref prop mid_1...mid_max conc mid_1...mid_max prop suff 
#
# thus: max_dist *2 + 5 elements ( the 5 extra elements being: initial
# pref, first prop, concept, last prop, suffix)
#
# we need 4 arrays to represent 4 types of information about the
# window elements, namely: property/concept representation; context
# representation (how the word will look like if it is used as part of
# a pattern); status flags ( that takes values: 0: not possible prop;
# >0: possible prop; >1 concept); pos suffix (to be appended to
# properties in the output)

my @pattern_representations = ();
my @target_representations = ();
my @status_flags = ();
my @pos_suffixes = ();
my $last_index = ($max_dist *2) + 4; # 4 because we start counting from 0!
# the target is in the middle:
my $target_index = $max_dist +2;


# initial padding
for (my $i = 0; $i < $target_index; $i++) {
    $pattern_representations[$i] = "SENT";
    $target_representations[$i] = "SENT";
    $status_flags[$i] = 0;
    $pos_suffixes[$i] = "X";
}

# optional noun keep list
# in format:
# lowercased-inflected-form
my %keep_nouns = ();
if ($opts{n}) {
    open KEEP,$opts{n} or die "could not open file $opts{n}";
    while (<KEEP>) {
	chomp;
	$keep_nouns{$_} = 1;
    }
    close KEEP;
}


# optional verb keep list
# in format:
# verbal-lemma
my %keep_verbs = ();
if ($opts{v}) {
    open KEEP,$opts{v} or die "could not open file $opts{v}";
    while (<KEEP>) {
	chomp;
	$keep_verbs{$_} = 1;
    }
    close KEEP;
}


# optional adj keep list
# in format:
# adjectival-lemma
my %keep_adjs = ();
if ($opts{j}) {
    open KEEP,$opts{j} or die "could not open file $opts{j}";
    while (<KEEP>) {
	chomp;
	$keep_adjs{$_} = 1;
    }
    close KEEP;
}
# because of a bug in the treetagger (or a funny tagging choice)
# such in such as is labeled as adj, so we must add "such" to
# the adj list in order not to lose it
$keep_adjs{"such"} = 1;



# optional adv keep list
# in format:
# adverbial-lemma
my %keep_advs = ();
if ($opts{r}) {
    open KEEP,$opts{r} or die "could not open file $opts{r}";
    while (<KEEP>) {
	chomp;
	$keep_advs{$_} = 1;
    }
    close KEEP;
}


# optional stop list, in format
# lemma pos (where, however, pos is simply n, j or v!!!)
my %stop = ();
if ($opts{s}) {
    open STOP,$opts{s} or die "could not open file $opts{s}";
    while (<STOP>) {
	chomp;
	my (@F) = split "[\t ]+",$_; 
	$stop{$F[0]} = $F[1];
    }
}



##################### end of parameter initialization #####################

##################### corpus traversal #####################

$| = 1;

while (<>) {
    chomp;

    # let's get word, pos and lemma
    my ($word,$pos,$lemma) = split "[\t ]+",$_;
    
    # we wil keep track of whether word is concept, property or neither
    my $flag = 0;

    # also, for potential properties we will append a pos suffix
    my $pos_suffix = "X";

    # is this a concept? add value 1 to flag list (we will add 1
    # in next step because it should be a noun, adj or verb)
    if ($pos =~/CONCEPT/) {
	$flag = 1;
    }

    # is this a potential property? a potential property is a noun,
    # adj or full verb, and it contains alphabetical characters and -
    # only (furthermore, there is only one dash, and it is not at
    # the beginning, nor at the end)
    if (($lemma !~/[^a-zA-Z\-]/) && ($lemma !~/\-.*\-/) &&
	($lemma !~/^\-/) && ($lemma !~/\-$/) &&
	($pos =~/^(JJ|VV|NN)/)) {
	if ($1 eq "JJ") {
	    $pos_suffix = "-j";
	}
	elsif ($1 eq "VV") {
	    $pos_suffix = "-v";
	}
	else {
	    $pos_suffix = "-n";
	}
	
	$flag += 1;
    }
    # if form is verb, adj or noun, we have to assign
    # appropriate suffix in any case, because it is going
    # to act as filter below
    if (($pos =~/^(JJ|VV|NN)/)) {
	if ($1 eq "JJ") {
	    $pos_suffix = "-j";
	}
	elsif ($1 eq "VV") {
	    $pos_suffix = "-v";
	}
	else {
	    $pos_suffix = "-n";
	}
    }


    # add to flag array
    push @status_flags,$flag;
    # also, ass suffix to pos suffix array
    push @pos_suffixes,$pos_suffix;

    # push lemma "as is" in target representation (this will
    # be ignored for non targets anyway)
    push @target_representations,$lemma;

    # if word is verb or adjective, use pos only as part of the pattern,
    # unless relevant lemma is in relevant keep list
    if ($pos_suffix eq "\-v") {
	if (!$keep_verbs{$lemma}) {
	    $word = "";
	}
    }
    if ($pos_suffix eq "\-j") {
	if (!$keep_adjs{$lemma}) {

	    $word = "";
	}
    }
    # adverbs are not potential properties, but we also keep lemma
    # only if it is in keep list
    if ($pos =~ /^RB/) {
	if (!$keep_advs{$lemma}) {
	    $word = "";
	}
    }
    # for cardinal numbers we do not keep the number in any case
    if ($pos =~ /^CD/) {
	$word = "";
    }    

    # add lower-cased version of word (or nothing in the cases above)
    # pos and lemma (or nothing in the cases above) to pattern
    # representation (after stripping the "CONCEPT" part of pos, if
    # present, and converting "an" to "a") also, replace any _ with -
    # (or else _ might get confused with _ as a delimiter inside the
    # patterns)
    $pos =~ s/CONCEPT//;
    if ($word eq "an") {
	$word = "a";
	$lemma = "a";
    }
    $word =~ s/_/\-/g;
    $lemma =~ s/_/\-/g;
    if ($word eq "") {
	$lemma = "";
    }

    push @pattern_representations, lc($word) . "\/" . $pos . "\/" . lc($lemma);

    # if all window positions are full, we collect co-occurrences
    # and then we shift to remove first element
    if (defined($pattern_representations[$last_index])) {
	print_tuples();
	shift @pattern_representations;
	shift @target_representations;
	shift @status_flags;
	shift @pos_suffixes;
    }
}

# final flushing

my $remainder = $last_index - $target_index;
while ($remainder > 0) {

    push @pattern_representations,"SENT";
    push @target_representations,"SENT";
    push @status_flags,0;
    push @pos_suffixes,"X";

    print_tuples();

    shift @pattern_representations;
    shift @target_representations;
    shift @status_flags;
    shift @pos_suffixes;

    $remainder--;
}

##################### end of corpus traversal #####################


##################### subroutines #####################

# routine print_tuples, where most of the 
# action happens
sub print_tuples{
    
    # first, let's see if current target is concept, if not
    # we move on
    if ($status_flags[$target_index] < 2) {
	return;
    }

    # OK, we're in, let's get the pos of the current target
    my $concept_pos = $pattern_representations[$target_index];
    $concept_pos =~ s/^[^\/]*\///;
    $concept_pos =~ s/\/.*$//;

    # first, we must restrict window to go from word to the right of
    # first sent boundary to the left of word to the left of last sent
    # boundary
    my $sent_before = $target_index - 1;
    while ($sent_before > 0) {
	if ($pattern_representations[$sent_before] eq "SENT") {
	    last;
	}
	$sent_before--;
    }
    
    my $sent_after = $target_index + 1;
    while ($sent_after < $#pattern_representations) {
	if ($pattern_representations[$sent_after] eq "SENT") {
	    last;
	}
	$sent_after++;
    }


    # the actual window we explore will go from first property
    # after sent_before to last feature before sent_after
    my $leftmost = $sent_before + 1;
    while ($status_flags[$leftmost] < 1) {
	$leftmost++;
	if ($leftmost == $target_index) {
	    last;
	}
    }

    my $rightmost = $sent_after - 1;
    while ($status_flags[$rightmost] < 1) {
	$rightmost--;
	if ($rightmost == $target_index) {
	    last;
	}
    }

    # now, we traverse from leftmost to target-1 and from target+1 and
    # rightmost, and, for any margin item that is a potential
    # property, we check whether we should print
    
    # first property-concept
    my $i = $leftmost;
    while ($i < $target_index) {
	# is current item a potential property, not in stop list (with
	# relevant pos?), and, if noun, not identical to current
	# target?
	if ($status_flags[$i] == 0) {
	    $i++;
	    next;
	}
	my $pos_of_potential_property = "";
	if ($pos_of_potential_property = $stop{$target_representations[$i]}) {
	    if ($pos_of_potential_property eq "\-" . $pos_suffixes[$i]) {
		$i++;
		next;
	    }
	}
	if (($pos_suffixes[$i] eq "\-n") &&
	    ($target_representations[$target_index] 
	     eq $target_representations[$i])) {
	    $i++;
	    next;
	}
	# if none of these filters applied, we will create a middle
	# string by concatenating the items between current item and
	# the target concept in the pattern array unless the current
	# item is adjacent to the concept, in which case middle string
	# will just be "_"
	my $middle = "_";
	if (($target_index-$i)>1) {
	    $middle = 
		join "_",
		@pattern_representations[$i+1..$target_index-1];
	}

	# we also extract the pos of the property
	my $property_pos = $pattern_representations[$i];
	$property_pos =~ s/^[^\/]*\///;
	$property_pos =~ s/\/.*$//;

	# now, if the constraints on the possible patterns are met,
	# we print one output line
	if (check_pattern($pos_suffixes[$i],
			  $concept_pos,$property_pos,
			  "right",$pattern_representations[$i-1],
			  $middle,
			  $pattern_representations[$target_index+1])) {
	    print $target_representations[$target_index],"\t";
	    print $target_representations[$i],$pos_suffixes[$i],"\t";
	    print $middle,"\+right\+",$concept_pos,"\+",$property_pos,"\n";
	}

	$i++;
    }

    # now we go from the concept rightwards
    $i = $target_index + 1;
    while ($i <= $rightmost) {
	# is current item a potential property, not in stop list (with
	# relevant pos) and different from current target concept?
	# is current item a potential property, not in stop list (with
	# relevant pos?), and, if noun, not identical to current
	# target?
	if ($status_flags[$i] == 0) {
	    $i++;
	    next;
	}
	my $pos_of_potential_property = "";
	if ($pos_of_potential_property = $stop{$target_representations[$i]}) {
	    if ($pos_of_potential_property eq "\-" . $pos_suffixes[$i]) {
		$i++;
		next;
	    }
	}
	if (($pos_suffixes[$i] eq "\-n") &&
	    ($target_representations[$target_index] 
	     eq $target_representations[$i])) {
	    $i++;
	    next;
	}

	# all filters ok? then let's concatenate middle, as above
	my $middle = "_";
	if (($i-$target_index)>1) {
	    $middle = 
		join "_", 
		@pattern_representations[$target_index+1..$i-1];
	}
	# pos of the property
	my $property_pos = $pattern_representations[$i];
	$property_pos =~ s/^[^\/]*\///;
	$property_pos =~ s/\/.*$//;
	
	# now, if the constrains on the possible patterns are met,
	# we print one output line
	if (check_pattern($pos_suffixes[$i],
			  $concept_pos,$property_pos,
			  "left",$pattern_representations[$target_index-1],
			  $middle,
			  $pattern_representations[$i+1])) {
	    print $target_representations[$target_index],"\t";
	    print $target_representations[$i],$pos_suffixes[$i],"\t";
	    print $middle,"\+left\+",$concept_pos,"\+",$property_pos,"\n";
	}
	
	$i++;
    }
}

# routine check_pattern, that encodes our "linguistic knowledge" about
# plausible patterns connecting a nominal concept to potential
# properties expressed by adjectives, nouns and verbs 

# this is totally hard-coded, and it would be cool to have the
# filtering done via a parameter file written in some sort of
# "grammar", but it would also be a lot of work!

sub check_pattern{
    my $property_simplified_pos = shift;
    my $concept_pos = shift;
    my $property_pos = shift;
    my $conceptposition = shift;
    my $left_side = shift;
    my $middle = shift;
    my $right_side = shift;

    # left and right side and middle contain a lemma, that is useful when
    # printing out the pattern, but not to check its validity, so we 
    # must strip it off
    $left_side =~ s/(\/.*)\/.*$/$1/;
    $right_side =~ s/(\/.*)\/.*$/$1/;

    if ($middle ne "_") {
	my @temp_middle = split "_",$middle;
	my @temp_cleaned_middle = ();
	foreach my $middle_component (@temp_middle) {
	    $middle_component =~ s/(\/.*)\/.*$/$1/;
	    push @temp_cleaned_middle,$middle_component;
	}
	$middle = join "_",@temp_cleaned_middle;
    }

    my $ok_pattern = 0;

    # different rules apply to different categories of properties
    # nouns
    if ($property_simplified_pos eq "\-n") {
	$ok_pattern = filter_noun_properties($concept_pos,$property_pos,
					     $conceptposition,$left_side,
					     $middle,$right_side);
    }
    # adjectives
    if ($property_simplified_pos eq "\-j") {
	$ok_pattern = filter_adj_properties($concept_pos,$property_pos,
					    $conceptposition,$left_side,
					    $middle,$right_side);
    }
    # verbs
    if ($property_simplified_pos eq "\-v") {
	$ok_pattern = filter_verb_properties($concept_pos,$property_pos,
					     $conceptposition,$left_side,
					     $middle,$right_side);
    }

    return $ok_pattern;
}

# routine filter_noun_properties, that applies constraints specific to
# patterns connecting a concept with a noun as potential property
sub filter_noun_properties {

    my $concept_pos = shift;
    my $property_pos = shift;
    my $conceptposition = shift;
    my $left_side = shift;
    my $middle = shift;
    my $right_side = shift;


    # first, some rules that apply to all properties
    if (!filter_all($concept_pos,$property_pos,
		    $conceptposition,$left_side,
		    $middle,$right_side)) {
	return 0;
    }

    # on the right we cannot have a noun, adjective,
    # possessive, or pronoun
    if ($right_side =~ /\/(N|J|POS)/ || $right_side =~ /\/PP$/) {
	return 0;
    }

    # the N N compound case
    if ($middle eq "_") {
	return 1;
    }

    # one of the following pos's must be part of the pattern, in order
    # to guarantee that it is some sort of connector
    if ($middle !~ /\/(IN|PDT|POS|VH|VV|WP\$)/) {
	return 0;
    }

    # if there are nouns, the following conditions must apply:
    if ($middle =~ /NN/) {
	# - maximally 1 noun
	if ($middle =~ /NN.*NN/) {
	    return 0;
	}
	# - noun must be surrounded by prepositions
	if ($middle !~ /IN.*NN.*IN/) {
	    return 0;
	}
	# - noun must be from target noun list
	my $middle_noun = $middle;
	$middle_noun =~ s/^.*_([^_]+)\/NN.*/$1/;
	if (!$keep_nouns{$middle_noun}) {
	    return 0;
	}
    }

    # if we made it down here, we are dealing with well-formed
    # pattern
    return 1;

}


# routine filter_adj_properties, that applies constraints specific to
# patterns connecting a concept with an adjective as potential property
sub filter_adj_properties {

    my $concept_pos = shift;
    my $property_pos = shift;
    my $conceptposition = shift;
    my $left_side = shift;
    my $middle = shift;
    my $right_side = shift;

    # first, some rules that apply to all properties
    if (!filter_all($concept_pos,$property_pos,
		    $conceptposition,$left_side,
		    $middle,$right_side)) {
	return 0;
    }

    # on the right we cannot have a noun, adjective,
    # possessive, or pronoun
    if ($right_side =~ /\/(N|J|POS)/ || $right_side =~ /\/PP$/) {
	return 0;
    }
    
    # now, we deal with the ADJ NOUN case, where only adjacency is
    # allowed
    if ($conceptposition eq "right") {
	if ($middle eq "_") {
	    return 1;
	}
	return 0;
    }

    # now, the NOUN COPULA ADJ CASE

    # copula must be present
    if ($middle !~ /\/VB/) {
	return 0;
    }
    
    # the following elements cannot occur in the middle
    if ($middle =~ 
	/\/(\(|\)|:|DT|IN|N|P|TO|VV|W)/) {
	return 0;
    }

    # if we got down here, the patter is well-formed
    return 1;
}

# routine filter_verb_properties, that applies constraints specific to
# patterns connecting a concept with a verb as potential property
sub filter_verb_properties {

    my $concept_pos = shift;
    my $property_pos = shift;
    my $conceptposition = shift;
    my $left_side = shift;
    my $middle = shift;
    my $right_side = shift;


    # first, some rules that apply to all properties
    if (!filter_all($concept_pos,$property_pos,
		    $conceptposition,$left_side,
		    $middle,$right_side)) {
	return 0;
    }

    # the VERB NOUN case
    if ($conceptposition eq "right") {

	# on the right we cannot have a noun, adjective,
	# possessive, or pronoun
	if ($right_side =~ /\/(N|J|POS)/ || $right_side =~ /\/PP$/) {
	    return 0;
	}
	
	# elements that should not occur between verb and noun
	if ($middle =~ /\/(\(|\)|:|N|V|W)/) {
	    return 0;
	}

	# if we got here, pattern is well-formed
	return 1;
    }

    # now, the NOUN VERB case

    # if verb pos is VVD or VVN, "to" should not be the following item
    # (to avoid things like "intended to")
    if (($property_pos =~ /VV(D|N)/) &&
	($right_side =~/TO/)) {
	return 0;
    }

    # elements that should not occur between verb and noun
    if ($middle =~ /\/(\(|\)|:|IN|J|N|PDT|POS|RBR|RBS|VV)/) {
	return 0;
    }
    
    # if we got here, pattern is well-formed
    return 1;
}

# filter_all routine, it applies some general constraints that are
# valid no matter what is the pos of the potential property
sub filter_all {
    my $concept_pos = shift;
    my $property_pos = shift;
    my $conceptposition = shift;
    my $left_side = shift;
    my $middle = shift;
    my $right_side = shift;
    
    # list of POSs that can never be part of the  middle
    if ($middle =~ /\/(\,|\#|\$|CC|EX|FW|LS|NP|NPS|PP|RP|SENT|SYM|UH)/) {
	return 0;
    }

    # moreover, the cumulative word part of the middle, when non
    # empty, cannot be entirely non-alphabetical (a-z should suffice
    # since words have been lower-cased, and POSs are all upper-case)
    my @words_poss = ();
    
    @words_poss = split "_",$middle;
    foreach (@words_poss) {
	# empty word, no problem
	if (/^\//) {
	    next;
	}

	my ($w,$p) = split "[\/]",$_;
	if ($w !~ /[a-z]/) {
	    return 0;
	}
    }

    # if we got here, we are fine as far as general constraints go
    return 1;

}


##################### end of subroutines #####################


