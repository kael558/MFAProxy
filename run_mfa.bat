echo "Running MFA"
call conda activate aligner

call mfa align --clean inputs/ japanese_mfa japanese_mfa outputs/

call conda deactivate
