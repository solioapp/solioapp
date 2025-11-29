/**
 * Solio - Wallet Integration
 * Handles Solana wallet connections and transactions
 */

// ============================================
// Wallet State
// ============================================
let connectedWallet = null;
let walletPublicKey = null;

// Platform wallet address (loaded from API)
let platformWalletAddress = null;

// ============================================
// Initialization
// ============================================
document.addEventListener('DOMContentLoaded', async () => {
    // Load platform info
    try {
        const response = await fetch('/api/platform-info');
        const data = await response.json();
        platformWalletAddress = data.platform_wallet;
    } catch (error) {
        console.error('Failed to load platform info:', error);
    }

    // Initialize wallet options
    initWalletOptions();

    // Check for auto-connect
    checkAutoConnect();
});

// ============================================
// Wallet Detection
// ============================================
function getAvailableWallets() {
    const wallets = [];

    if (window.solana?.isPhantom) {
        wallets.push({
            name: 'phantom',
            displayName: 'Phantom',
            provider: window.solana
        });
    }

    if (window.solflare?.isSolflare) {
        wallets.push({
            name: 'solflare',
            displayName: 'Solflare',
            provider: window.solflare
        });
    }

    if (window.backpack) {
        wallets.push({
            name: 'backpack',
            displayName: 'Backpack',
            provider: window.backpack
        });
    }

    return wallets;
}

// ============================================
// Wallet Options UI
// ============================================
function initWalletOptions() {
    const walletOptions = document.querySelectorAll('.wallet-option');

    walletOptions.forEach(option => {
        const walletName = option.dataset.wallet;

        option.addEventListener('click', async () => {
            await connectWallet(walletName);
        });
    });
}

// ============================================
// Auto Connect
// ============================================
async function checkAutoConnect() {
    // Check if user previously connected
    const savedWallet = localStorage.getItem('solio_wallet');

    if (savedWallet) {
        const wallets = getAvailableWallets();
        const wallet = wallets.find(w => w.name === savedWallet);

        if (wallet && wallet.provider.isConnected) {
            try {
                const response = await wallet.provider.connect({ onlyIfTrusted: true });
                connectedWallet = wallet;
                walletPublicKey = response.publicKey.toString();
                updateWalletUI(true);
            } catch {
                // User hasn't previously connected, ignore
            }
        }
    }
}

// ============================================
// Connect Wallet
// ============================================
async function connectWallet(walletName) {
    const wallets = getAvailableWallets();
    const wallet = wallets.find(w => w.name === walletName);

    if (!wallet) {
        // Wallet not installed
        const urls = {
            phantom: 'https://phantom.app/',
            solflare: 'https://solflare.com/',
            backpack: 'https://backpack.app/'
        };

        if (urls[walletName]) {
            window.open(urls[walletName], '_blank');
        }
        showToast(`${walletName} is not installed`, 'warning');
        return null;
    }

    try {
        showLoading('Connecting wallet...');

        const response = await wallet.provider.connect();

        // Handle different wallet response formats
        let publicKey;
        if (response && response.publicKey) {
            publicKey = response.publicKey.toString();
        } else if (wallet.provider.publicKey) {
            publicKey = wallet.provider.publicKey.toString();
        } else {
            throw new Error('Could not get public key from wallet');
        }

        connectedWallet = wallet;
        walletPublicKey = publicKey;

        // Save preference
        localStorage.setItem('solio_wallet', walletName);

        // Close modal
        const modal = document.getElementById('walletModal');
        if (modal) modal.classList.remove('active');

        // Authenticate with backend
        showLoading('Authenticating...');
        await authenticateWithWallet(publicKey);

        updateWalletUI(true);
        hideLoading();

        return publicKey;

    } catch (error) {
        hideLoading();
        console.error('Wallet connection error:', error);
        showToast('Failed to connect wallet', 'error');
        return null;
    }
}

// ============================================
// Disconnect Wallet
// ============================================
async function disconnectWallet() {
    if (connectedWallet) {
        try {
            await connectedWallet.provider.disconnect();
        } catch {
            // Ignore disconnect errors
        }
    }

    connectedWallet = null;
    walletPublicKey = null;
    localStorage.removeItem('solio_wallet');

    updateWalletUI(false);
}

// ============================================
// Authenticate with Backend
// ============================================
async function authenticateWithWallet(publicKey) {
    try {
        // Get nonce from backend
        const nonceResponse = await fetchWithCsrf('/auth/wallet/nonce', {
            method: 'POST',
            body: JSON.stringify({ wallet_address: publicKey })
        });

        if (!nonceResponse.ok) {
            throw new Error('Failed to get nonce');
        }

        const nonceData = await nonceResponse.json();
        const message = nonceData.message;

        // Sign message
        const encodedMessage = new TextEncoder().encode(message);
        const signedMessage = await connectedWallet.provider.signMessage(encodedMessage, 'utf8');

        // Convert signature to base58
        let signature;
        const signatureBytes = signedMessage.signature || signedMessage;
        // Use our custom base58Encode function
        signature = window.base58Encode(signatureBytes);

        // Verify with backend
        const verifyResponse = await fetchWithCsrf('/auth/wallet/verify', {
            method: 'POST',
            body: JSON.stringify({
                wallet_address: publicKey,
                signature: signature,
                nonce: nonceData.nonce
            })
        });

        if (!verifyResponse.ok) {
            const error = await verifyResponse.json();
            throw new Error(error.error || 'Verification failed');
        }

        const userData = await verifyResponse.json();
        showToast('Successfully logged in!', 'success');

        // Reload page to update UI
        setTimeout(() => window.location.reload(), 500);

        return userData;

    } catch (error) {
        console.error('Authentication error:', error);
        showToast(error.message || 'Authentication error', 'error');
        throw error;
    }
}

// ============================================
// Update UI
// ============================================
function updateWalletUI(connected) {
    const connectBtn = document.getElementById('connectWalletBtn');

    if (connectBtn) {
        if (connected && walletPublicKey) {
            connectBtn.innerHTML = `
                <span>${truncateWallet(walletPublicKey)}</span>
            `;
            connectBtn.onclick = disconnectWallet;
        } else {
            connectBtn.innerHTML = `
                <svg viewBox="0 0 24 24" width="18" height="18">
                    <path fill="currentColor" d="M21 18v1c0 1.1-.9 2-2 2H5c-1.11 0-2-.9-2-2V5c0-1.1.89-2 2-2h14c1.1 0 2 .9 2 2v1h-9c-1.11 0-2 .9-2 2v8c0 1.1.89 2 2 2h9zm-9-2h10V8H12v8zm4-2.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
                </svg>
                Connect Wallet
            `;
        }
    }
}

// ============================================
// Ensure Wallet Connected
// ============================================
async function ensureWalletConnected() {
    // Already connected
    if (connectedWallet && walletPublicKey) {
        return true;
    }

    // Try to reconnect from saved preference
    const savedWallet = localStorage.getItem('solio_wallet');
    if (savedWallet) {
        const wallets = getAvailableWallets();
        const wallet = wallets.find(w => w.name === savedWallet);

        if (wallet) {
            try {
                const response = await wallet.provider.connect();
                let publicKey;
                if (response && response.publicKey) {
                    publicKey = response.publicKey.toString();
                } else if (wallet.provider.publicKey) {
                    publicKey = wallet.provider.publicKey.toString();
                }

                if (publicKey) {
                    connectedWallet = wallet;
                    walletPublicKey = publicKey;
                    return true;
                }
            } catch (e) {
                console.log('Auto-reconnect failed:', e);
            }
        }
    }

    return false;
}

// ============================================
// Make Donation
// ============================================
async function makeDonation(projectId, amountSOL, message = '', rewardTierId = '', donorEmail = '') {
    // Try to ensure wallet is connected
    const isConnected = await ensureWalletConnected();

    if (!isConnected) {
        // Open wallet modal
        const modal = document.getElementById('walletModal');
        if (modal) modal.classList.add('active');
        throw new Error('Please connect your wallet');
    }

    if (!platformWalletAddress) {
        throw new Error('Platform is not configured properly');
    }

    let currentStep = 'prepare';
    let isDevnet = false;
    let signature = null;

    try {
        // Show progress modal instead of loading spinner
        showTxProgress();
        setTxStep('prepare');

        // Create transaction using Solana web3.js
        const { Connection, PublicKey, Transaction, SystemProgram, LAMPORTS_PER_SOL } = solanaWeb3;

        // Get RPC URL from backend config
        const platformInfo = await fetch('/api/platform-info').then(r => r.json());
        isDevnet = platformInfo.use_devnet;
        const rpcUrl = platformInfo.rpc_url;

        const connection = new Connection(rpcUrl, {
            commitment: 'confirmed',
            confirmTransactionInitialTimeout: 120000
        });

        const fromPubkey = new PublicKey(walletPublicKey);
        const toPubkey = new PublicKey(platformWalletAddress);
        const lamports = Math.floor(amountSOL * LAMPORTS_PER_SOL);

        // Step 2: Sign transaction
        currentStep = 'sign';
        setTxStep('sign');

        // Get fresh blockhash right before signing to maximize valid block window
        const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash('finalized');

        // Create transfer instruction
        const transaction = new Transaction().add(
            SystemProgram.transfer({
                fromPubkey,
                toPubkey,
                lamports
            })
        );

        transaction.feePayer = fromPubkey;
        transaction.recentBlockhash = blockhash;

        // Sign and send transaction
        const result = await connectedWallet.provider.signAndSendTransaction(transaction, {
            skipPreflight: false,
            preflightCommitment: 'confirmed',
            maxRetries: 5
        });
        signature = result.signature;

        // Step 3: Sending
        currentStep = 'send';
        setTxStep('send');
        setTxSignature(signature, isDevnet);

        // Step 4: Confirming
        currentStep = 'confirm';
        setTxStep('confirm');

        // Robust confirmation with polling fallback
        const confirmed = await confirmTransactionWithRetry(connection, signature, blockhash, lastValidBlockHeight);

        if (!confirmed) {
            // Transaction may still process - check one more time
            console.warn('Initial confirmation failed, doing final status check...');
            const finalStatus = await connection.getSignatureStatus(signature);
            if (finalStatus?.value?.err) {
                throw new Error('Transaction failed: ' + JSON.stringify(finalStatus.value.err));
            }
            // If no error, assume pending/processing and continue to verification
            console.log('Transaction may still be processing, proceeding to verification...');
        }

        // Step 5: Verify with backend
        currentStep = 'verify';
        setTxStep('verify');

        const verifyResponse = await fetchWithCsrf('/donations/verify', {
            method: 'POST',
            body: JSON.stringify({
                project_id: projectId,
                tx_signature: signature,
                amount_sol: amountSOL.toString(),
                donor_wallet: walletPublicKey,
                message: message,
                reward_tier_id: rewardTierId || null,
                donor_email: donorEmail || null
            })
        });

        if (!verifyResponse.ok) {
            const error = await verifyResponse.json();
            throw new Error(error.error || 'Donation verification failed');
        }

        const verifyResult = await verifyResponse.json();

        // Mark verify as completed
        setTxStep('verify');
        document.querySelector('[data-step="verify"]')?.classList.add('completed');

        // Show success
        showToast('Donation sent successfully!', 'success');

        // Update UI
        updateProjectStats(verifyResult.project);

        // Close modal and reload after short delay
        setTimeout(() => {
            hideTxProgress();
            window.location.reload();
        }, 2000);

        return verifyResult;

    } catch (error) {
        console.error('Donation error:', error);

        // Show error on current step
        setTxError(currentStep);

        if (error.message.includes('User rejected')) {
            showToast('Transaction was cancelled', 'warning');
        } else if (error.message.includes('BlockheightExceeded') || error.message.includes('block height')) {
            showToast('Network congestion - please try again', 'error');
        } else {
            showToast(error.message || 'Donation error', 'error');
        }

        // Hide modal after delay
        setTimeout(() => hideTxProgress(), 3000);

        throw error;
    }
}

// ============================================
// Robust Transaction Confirmation
// ============================================
async function confirmTransactionWithRetry(connection, signature, blockhash, lastValidBlockHeight) {
    const maxAttempts = 30;
    const pollIntervalMs = 2000;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
            // First check signature status directly (faster)
            const status = await connection.getSignatureStatus(signature);

            if (status?.value?.confirmationStatus === 'confirmed' ||
                status?.value?.confirmationStatus === 'finalized') {
                console.log(`Transaction confirmed after ${attempt + 1} attempts`);
                return true;
            }

            if (status?.value?.err) {
                throw new Error('Transaction failed: ' + JSON.stringify(status.value.err));
            }

            // Check if blockhash is still valid
            const currentBlockHeight = await connection.getBlockHeight('confirmed');
            if (currentBlockHeight > lastValidBlockHeight) {
                console.warn('Block height exceeded, but signature may still be valid');
                // Don't throw - the transaction might still confirm
            }

            // Wait before next poll
            await new Promise(resolve => setTimeout(resolve, pollIntervalMs));

        } catch (pollError) {
            console.warn(`Confirmation poll attempt ${attempt + 1} failed:`, pollError.message);
            // Continue polling unless it's a definitive failure
            if (pollError.message.includes('Transaction failed')) {
                throw pollError;
            }
            await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
        }
    }

    // Final check after all attempts
    const finalStatus = await connection.getSignatureStatus(signature);
    if (finalStatus?.value?.confirmationStatus === 'confirmed' ||
        finalStatus?.value?.confirmationStatus === 'finalized') {
        return true;
    }

    console.warn('Transaction confirmation timed out after all attempts');
    return false;
}

// ============================================
// Update Project Stats (after donation)
// ============================================
function updateProjectStats(project) {
    // Update raised amount
    const fundingAmount = document.querySelector('.funding-amount .raised');
    if (fundingAmount) {
        fundingAmount.textContent = formatSOL(project.raised_sol);
    }

    // Update progress bar
    const progressFill = document.querySelector('.progress-bar .progress-fill');
    if (progressFill) {
        progressFill.style.width = `${Math.min(project.progress_percent, 100)}%`;
    }

    // Update donation count
    const donationStat = document.querySelector('.funding-stats .stat:nth-child(2) .stat-value');
    if (donationStat) {
        donationStat.textContent = project.donation_count;
    }
}

// Make functions globally available
window.connectWallet = connectWallet;
window.disconnectWallet = disconnectWallet;
window.makeDonation = makeDonation;
window.getAvailableWallets = getAvailableWallets;
