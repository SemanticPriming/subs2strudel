#!/usr/bin/perl -w

use strict "vars";
use Getopt::Std;

# ADD COMMENTS

my $usage;
{
$usage = <<"_USAGE_";

This script takes as input a list of tuples in format

concept property pattern score

where concept, property and pattern follow the output specification of
strudel-parser.pl, and the score could, e.g., be a count of the
occurrences of the tuple.

Output is in format:

concept property gentype score

where concept, property and score are unmodified, and gentype is a
generalization of the pattern to a StruDEL generalized type. Note that
in some cases, in which the pattern has no proper generalization, the
tuple is skipped in the output.

The generalization rules are currently hard-coded in the script, see
comments in the code. The rules implemented in this version are
described in the technical report about StruDEL available on the
StruDEL website.

The only option to the script is:

-h: print this documentation and exit

Usage:

map-patterns-to-types.pl -h | more

map-patterns-to-types.pl tuples > gentuples

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


my %opts = ();

getopts('h',\%opts);

if ($opts{h}) {
    print $usage;
    exit;
}



my $pattern_file = shift;


open PATTERNS,$pattern_file;
while (<PATTERNS>) {

    chomp;

    my $full_string = $_;

    my @F = split "[\t ]+",$full_string;

    my @components = split "[\+]",$F[2];

    my $core = "";
    my $suffix = "";


    if ($F[1] =~ /\-n$/) {
	$core = extract_nominal_core($components[0],$components[1]);
	$suffix = "n";
    }
    elsif ($F[1] =~ /\-j$/) {
	$core = extract_adjectival_core($components[0],$components[1]);
	$suffix = "j";
    }
    elsif ($F[1] =~ /\-v$/) {
	$core = extract_verbal_core($components[0],$components[1]);
	$suffix = "v";
    }
    else {
	print STDERR 
	    "no expected property suffix for: $full_string, skipping...\n";
    }

      if (!$core) {
# 	print STDERR "no rule matched for: $full_string, skipping...\n";
 	next;
     }


    # print concept property core+concept_pos+suffix fq
    print join "\t",($F[0],$F[1],$core."\+".$components[1]."\+".$suffix,$F[3]);
    print "\n";
}
close PATTERNS;


sub extract_nominal_core {
    my $string = shift;
    my $position = shift;
    
    # rules to extract core of pattern
    
    my $core = "";
    
    # if connector is empty, skip
    if ($string eq "_") {
	$core = "";
#	$core = "_";
    }
    
    # whose (WP$): keep only that
    elsif ($string =~ /WP\$/) {
	$core = "WP\$";
    }
    
    # if there is a POS, that also takes priority
    elsif ($string =~ /POS/) {
	$core = "\'s";
    }
    
    # IN fullNN IN -> first in, unless it is of, in which case second
    # unless it is of, in which case skip --> (LAST OPTION NOT IN THIS
    # VERSION!)
    elsif ($string =~ /([^_]+)\/IN.*_[^_]+\/NN.*_([^_]+)\/IN/) {
	my $core = $1;
	if ($core eq "of") {
	    $core = $2;
	}
# 	if ($core eq "of") {
# 	    $core = "";
# 	}
    }

#    # if preposition is of, skip
#    elsif ($string =~ /(^|_)of\/IN/) {
#	$core = "";
#    }

    # fullVV IN (includes TO, like below) -> IN
    elsif ($string =~ /(^|_)([^_]+)\/VV.*_([^_]+)\/(IN|TO)/) {
	$core = $3;
    }

    # remaining fullVV
    elsif ($string =~ /(^|_)[^_]+\/VV[^\/]*\/([^_]+)/) {
	$core = $2;
    }

    # emptyVV IN -> IN
    elsif ($string =~ /VV.*_([^_]+)\/(IN|TO)/) {
	$core = $1;
    }

    # remaining VV: skip
    elsif ($string =~ /VV(.|$)/) {
	$core = "";
# 	my $pot_suff = $1;
# 	my $suff = "";
# 	if ($pot_suff =~ /[A-Z]/) {
# 	    $suff = $pot_suff;
# 	}
# 	$core = "VV" . $pot_suff;
    }

    # fullV(B|H) IN -> IN
    elsif ($string =~ /V(B|H).*_([^_]+)\/IN/) {
	$core = $2;
    }

    # such as
    elsif ($string =~ /such.*_as\//) {
	$core = "such_as";
    }

    # fullVB
    elsif ($string =~ /(^|_)([^_]+)\/VB/) {
	$core = "be";
    }
    
    # fullVH
    elsif ($string =~ /(^|_)([^_]+)\/VH/) {
	$core = "have";
    }

    # IN
    elsif ($string =~ /(^|_)([^_]+)\/(IN|TO)/) {
	$core = $2;
    }

    # PDT # only if not IN
    elsif ($string =~ /(^|_)([^_]+)\/PDT/) {
	$core = $2;
    }

    return $core;
}


sub extract_adjectival_core {
    my $string = shift;
    my $position = shift;
    
    # rules to extract core of pattern
    
    my $core = "";

    # first case: ADJ NOUN
    if ($position eq "right") {
	$core = "_";
    }

    # second case COPULA ADV ADJ
    elsif ($string =~ /RB/) {
	$core = "is_RB";
    }

    # third and last: COPULA ADJ
    else {
	$core = "is";
    }

    return $core;
}


sub extract_verbal_core {
    my $string = shift;
    my $position = shift;
    
    # rules to extract core of pattern
    
    my $core = "";

    # if noun is to the right and there is preposition,
    # use preposition as core
    if (($position eq "right") && ($string =~ /([^_]+)\/IN/)) {
	$core = $1;
    }

    # else, VERB NOUN or NOUN VERB
    else {
	$core = "_";
    }

    return $core;
}

