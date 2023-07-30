echo "Running MFA"
call conda activate aligner

call mfa align --clean inputs/ english_us_arpa english_us_arpa outputs/

call conda deactivate
