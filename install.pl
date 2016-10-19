#!/usr/bin/perl -w

my $installroot = "/opt";
my $installdir = "$installroot/indictools";
my $mongodbinstalldir = "$installroot/mongodb";

my $distdir = "$installdir/dist"; # Not used
my $srcdir = "$installdir";
my $bindir = "$installdir";
my $libdir = "$installdir/lib";
my $incdir = "$installdir/include";
my $wlcmongodbdir = "$installdir/wexplorer";
$bindir = $ENV{PWD} . "/$bindir" unless $bindir =~ m|^/|;
my $datadir = "$installdir/data";
my $datadir_wloads = "$datadir/workloads";
my $datadir_mongodb = "$datadir/mongodb";

my $verbose = 1;
my $dryrun = 0;
my $restart = 0;
my $force = 0;
my $upgrade = 0;
my $wlcpkgurl = ".";
#my $wlcgiturl = "xferuser\@10.113.208.77:/WorkSpace/git/indictools";
my $cmdpath = $0;
my $modules = "caffe,scan2text,samvit,mongodb";

my ($srcpath, $cmdname) = (".", $cmdpath);
($srcpath, $cmdname) = ($1, $2) if $cmdpath =~ /^(.*)\/(.*)$/;

my $usage = "Usage: 
  $cmdname -h (for help)
  $cmdname
  $cmdname [-n] [-f] [-i <packageurl>] [-o <installdir>]
    Install workload capture and analysis tools (a.k.a. indictools).
    Options:
    -n                Dry run; just print the commands to be run and exit.
    -f                Remove old installation and install afresh.
    -r                Forcibly restart indictools and mongodb.
    -u                Upgrade the existing installation.
    -m <module_names> [default: $modules].
                      Modules to install as a comma-separated list.
    -i <packageurl>   [default: $wlcpkgurl].
                      Get required packages from <packageurl>.
                      Within NetApp Engg, You can specify:
                          -i $wlcpkgurl_ntap.
    -o <installdir>   [default: $installdir].
                      Install tools into <installdir>.
";

while (@ARGV) {
    my $p = shift @ARGV;
    if ($p =~ /^-h/) {
        die $usage;
    }
    if ($p =~ /^-m/) {
        die $usage unless @ARGV;
        $modules = shift @ARGV;
    }
    elsif ($p =~ /^-n/) {
        $dryrun = 1;
    }
    elsif ($p =~ /^-f/) {
        $force = 1;
    }
    elsif ($p =~ /^-r/) {
        $restart = 1;
    }
    elsif ($p =~ /^-u/) {
        $upgrade = 1;
    }
    elsif ($p =~ /^-i/) {
        die $usage unless @ARGV;
        $wlcpkgurl = shift @ARGV;
    }
    elsif ($p =~ /^-o/) {
        die $usage unless @ARGV;
        $installdir = shift @ARGV;
    }
}

docmd("mkdir -p $installdir") ||
    die "Could not create install directory $installdir; exiting.\n"; 

$force = 0 if $upgrade;

print STDERR "Upgrading the existing WLC tools installation ...\n" if $upgrade;

if ($force) {
    # Delete everything in $installdir except data/ directory.
    print STDERR "Cleaning up $installdir (except data subdir) ...\n";
    foreach my $f (glob($installdir)) {
        next if $f == 'data';
        docmd("rm -rf $f");
    }
}

install_deps();

my $indictools_changed = 1;
if ($upgrade) {
    # Update from GIT source repository
	$indictools_changed = 0;
    if (-d $srcdir) {
        print STDERR "\nUpdating WLC tools in $srcdir ...\n";
#        print STDERR "When prompted for password, type 'transfer1'\n";
		my $git_out = `(cd $srcdir; git pull)`;
		$indictools_changed = 1 unless ($git_out =~ /up-to-date/);
		print STDERR $git_out;
        $restart = $restart || $indictools_changed;
    }
    exec "$srcdir/$cmdname -u " . ($restart ? "-r" : "") if $indictools_changed;
}
else {
    $restart = 1;
    # Install from dist
    if (-d "$wlcpkgurl") {
        print STDERR "\nInstalling software from \"$wlcpkgurl\" ...\n";
        $distdir = $wlcpkgurl;
    }
    else {
        print STDERR "\nDownloading install packages from $wlcpkgurl ...\n";
        print STDERR "When prompted for password, type 'transfer1'\n";
        docmd("rsync -av --partial --progress --delete $wlcpkgurl/ $distdir/") ||
            print STDERR "WARNING: Could not download support packages. Ignoring.\n";
    }

    if (-d "$distdir/indictools") {
        print STDERR "\nGetting indictools sources from $distdir/indictools ...\n";
        docmd("rsync -av --delete $distdir/indictools/ $srcdir/");
    }
    else {
        die "\nError: Cannot find $distdir/indictools; exiting.\n" unless $dryrun;
    }
}

if ($modules =~ /mongodb/) {
    $mongodb_changed = fix_mongodb();
    $restart = $restart || $mongodb_changed;
}

if ($modules =~ /samvit/) {
    docmd("rm -f /etc/init.d/samvit; cp $bindir/init-samvit.sh /etc/init.d/samvit");    
    docmd("update-rc.d samvit defaults");
}

docmd("chmod -R a+rwX $datadir");

if ($modules =~ /mongodb/) {
    print STDERR "\nCreating mongodb Data directory in $datadir_mongodb\n";
    docmd("mkdir -p $datadir_mongodb") ||
        print STDERR "Error: Could not create $datadir_mongodb\n";
}

print STDERR "\n" . ($upgrade ? "Upgrade" : "Installation") .
" completed successfully.
";

if ($modules =~ /samvit/ && $restart) {
    print STDERR "\nStarting Samvit web service ...\n";
    docmd("/etc/init.d/samvit restart");

    print STDERR
"Optional: To start an instance of Samvit service manually, run:
    $bindir/run-samvit.py -p <port#>
and point your web browser to the URL it indicates.
";
}
exit 0;

sub docmd
{
    my $cmd = shift;
    print STDERR "$cmd\n" if $verbose;
    return 1 if $dryrun;
    my $ret = system($cmd);
    print STDERR "failed\n" if $ret != 0;
    return $ret == 0;
}

sub is_installed
{
    my $cmd = shift;
    my $check = `which $cmd`;
    my $found = $check && ($check !~ m/(?:not found|denied)/mi);
    print STDERR "$cmd " . ($found ? "found" : "not found") . "\n";
    return $found;
}

sub install_deps
{
    print STDERR "\nInstalling prerequisite Linux packages ...\n";
    print STDERR "\nIf some packages are not found, try running 'apt-get update' and run this install script again\n";
    my $linux_distro = `lsb_release -a`;
    if ($linux_distro =~ m/(?:Ubuntu|Debian)/mi) {
        if ($modules =~ /indictools/) {
            docmd("apt-get -y install git mongodb") ||
                die "Error: Could not install required packages.\n";
        }
        if ($modules =~ /samvit/) {
            docmd("apt-get -y install python-pymongo python-dev python-pip python-flask") ||
                print STDERR "WARNING: Couldn't install python Flask needed for web UI.  Ignoring.\n";
        }
        if ($modules =~ /caffe/) {
            docmd("apt-get -y install git pkg-config g++ automake bzip2 make cmake cmake-qt-gui") ||
                print STDERR "WARNING: Couldn't install python Flask needed for web UI.  Ignoring.\n";
            docmd(" apt-get install -y libprotobuf-dev libleveldb-dev libsnappy-dev libopencv-dev libhdf5-serial-dev protobuf-compiler gfortran libjpeg62 libfreeimage-dev libatlas-base-dev git python-dev python-pip libgoogle-glog-dev libbz2-dev libxml2-dev libxslt-dev libffi-dev libssl-dev libgflags-dev liblmdb-dev python-yaml python-numpy build-essential git cmake cmake-curses-gui") ||
                print STDERR "WARNING: Couldn't install caffe; Ignoring.\n";
            docmd("apt-get -y install libboost1.55-all-dev");
        }
        docmd("apt-get -y install apache2 libapache2-mod-wsgi") ||
            print STDERR "WARNING: Couldn't install apache2 and wsgi modules.  Ignoring.\n";
    }
    elsif (is_installed("yum")) {
        if ($modules =~ /indictools/) {
            docmd("yum -y install git") ||
                print STDERR "Error installing some required packages.\n";
        }
        if ($modules =~ /samvit/) {
            docmd("yum -y install python-devel python-pip python-pymongo python-flask");
        }
    }
    else {
        die "Error: Linux package management software 'yum' not found; aborting.\n" 
            unless $dryrun;
    }
    docmd("pip install flask-restful") ||
        die "Error: Couldn't install Flask-restful needed for web UI.\n";
    docmd("pip install --upgrade pymongo") ||
        print STDERR "WARNING: Couldn't upgrade PyMongo to the latest version; ignoring.\n";
    return 1;
}

sub fix_mongodb
{
    my $changed = 0;
    return $changed unless -d $mongodbinstalldir;

    my $webconf = "/etc/mongodb.conf";
    my $fixed = 0;
    unless (-f $webconf) {
        docmd("touch $webconf") ||
            die "Cannot create $webconf\n";
    }
    $/ = undef;
    open(FH, $webconf);
    my $content = <FH>;
    close FH;
    my %adjustprops = (
        "dbpath" => "$mongodbinstalldir",
    );
    docmd("echo '[settings]' >> $webconf"); 
    foreach my $prop (keys %adjustprops) {
        my $setval = $adjustprops{$prop};
        if ($content =~ /^$prop\s*=\s*(.*)$/mi) {
            my $val = $1;
            print STDERR "mongodb config: $prop currently set to $val\n";
            if ($val ne $setval) {
                $changed = 1;
                system("ed -v $webconf << _EOF_
P
,s/\\($prop\\).*=.*/\\1 = $setval/p
w
_EOF_
");
            }
        }
        else {
            docmd("echo '$prop = $setval' >> $webconf");
            $changed = 1;
        }
    }

    print STDERR "Fixed mongodb config; will restart" if $changed;
    return $changed;
}
