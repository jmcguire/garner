#!/usr/bin/env perl
use strict;
use warnings;
use feature 'say';
use File::Path qw(make_path);
use Unicode::Normalize;

##
## This was a temporary script to split the single body.md file into the
## multiple files in definitions/ . I may delete this later.
##

my $input_file = shift or die "Usage: $0 input.md [output_dir]\n";
my $out_dir = shift // "definitions";

make_path($out_dir) unless -d $out_dir;

open my $in, '<:encoding(UTF-8)', $input_file
  or die "Cannot open $input_file: $!\n";

my $current_fh;
my $current_file;

while (my $line = <$in>) {

    if ($line =~ /^#\s+(.+?)\s*$/) {
        close $current_fh if $current_fh;

        my $heading = $1;
        my $filename = heading_to_filename($heading);

        $current_file = "$out_dir/$filename.md";

        die "file >$filename< already exists\n" if -e $current_file;

        open $current_fh, '>:encoding(UTF-8)', $current_file
          or die "Cannot write $current_file: $!\n";
    }

    print {$current_fh} $line if $current_fh;
}

close $current_fh if $current_fh;
close $in;

say "Done. Files written to $out_dir/";


sub heading_to_filename {
    my ($text) = @_;

    $text = NFD($text);
    $text =~ s/\p{NonspacingMark}//g;
    $text = lc $text;

    $text =~ s/# //;
    $text =~ s/ /-/g;

    $text =~ s/['",\.]/-/g;
    $text =~ s/[^\w\d-]//g;

    $text =~ s/^-+|-+$//g;
    $text =~ s/[-_]+/-/g;

    $text = substr($text, 0, 20);

    return $text || "untitled";
}
