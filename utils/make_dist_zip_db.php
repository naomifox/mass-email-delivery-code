<?php
    $scriptLines = file_get_contents("scriptlines.txt");
    $oldZipDict = file_get_contents("aarons_zip_per_dist.tsv");

    $zip4PerZip5 = array();
    $zipsPerDist = array();

    $oldZipDict = preg_replace("/ +/", "\t", $oldZipDict);
    $oldZipDictLines = explode("\n", $oldZipDict);
    foreach ($oldZipDictLines as $line) {
        $line = trim($line);
        $parts = explode("\t", $line);
        if (count($parts) > 1) {
            $zip4PerZip5[$parts[0]] = $parts[1];
        }
    }


    $scriptLines = preg_replace("/[ \t]+/", "\t", $scriptLines);
    $lines = explode("\n", $scriptLines);
    foreach ($lines as $line) {
        $line = trim($line);
        $parts = explode("\t", $line);
        if (count($parts) > 1) { 
            $zip5 = $parts[0];
            $distDef = $parts[1];
            if (strpos($distDef, "districts=") !== false) {
                $distArrDef = str_replace(";", "", str_replace("districts=", "", $distDef));
                $dists = json_decode($distArrDef, true);
                foreach ($dists as $dist) { 
                    $dist = substr($dist, 0, 2) . "-" . substr($dist, 2, 2);
                    if ( ! isset($zipsPerDist[$dist])) {
                        $zipsPerDist[$dist] = array();
                    }
                    $zipsPerDist[$dist][] = $zip5;
                }
            }
        }
    }

    foreach ($zipsPerDist as $dist => $zip5s) {
        $zip4 = "0001";
        $chosenZip5 = $zip5s[rand(0, count($zip5s) - 1)];
        foreach ($zip5s as $zip5) {
            if (isset($zip4PerZip5[$zip5])) {
                $zip4 = $zip4PerZip5[$zip5];
                $chosenZip5 = $zip5;
                break;
            }
        }
        echo "$chosenZip5\t$zip4\t$dist\n";
    }

?>