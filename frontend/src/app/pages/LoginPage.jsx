import React, { useState, useEffect, useRef } from 'react';

/**
 * ProExport - Production-Grade Auth Interface
 * Architectural Note: All hooks are at the top level to avoid React Hook errors.
 */

export default function LoginPage() {
    // --- ALL STATE DECLARED UPFRONT (per instructions) ---
    const [step, setStep] = useState(1);
    const [email, setEmail] = useState("");
    const [emailValid, setEmailValid] = useState(false);
    const [method, setMethod] = useState("password"); // Default method
    const [password, setPassword] = useState("");
    const [showPass, setShowPass] = useState(false);
    const [trustDevice, setTrustDevice] = useState(true);
    const [otp, setOtp] = useState(["", "", "", "", "", ""]);
    const [pin, setPin] = useState([]);
    const [bioState, setBioState] = useState("idle");
    const [timer, setTimer] = useState(60);
    const [timerActive, setTimerActive] = useState(false);
    const [attempts, setAttempts] = useState(0);
    const [locked, setLocked] = useState(false);
    const [lockTimer, setLockTimer] = useState(120);
    const [shake, setShake] = useState(false);
    const [oauthModal, setOauthModal] = useState(null);
    const [newDevice, setNewDevice] = useState(true);
    const [twoFAStep, setTwoFAStep] = useState(false);
    const [twoFACode, setTwoFACode] = useState(["", "", "", "", "", ""]);
    const [success, setSuccess] = useState(false);
    const [slideDir, setSlideDir] = useState("right");
    const [width, setWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1200);

    // --- REFS ---
    const otpRefs = [useRef(), useRef(), useRef(), useRef(), useRef(), useRef()];
    const twoFARefs = [useRef(), useRef(), useRef(), useRef(), useRef(), useRef()];
    const pinRef = useRef();

    // --- EFFECTS ---
    useEffect(() => {
        const handleResize = () => setWidth(window.innerWidth);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Timer Effect
    useEffect(() => {
        let interval;
        if (timerActive && timer > 0) {
            interval = setInterval(() => setTimer(prev => prev - 1), 1000);
        } else if (timer === 0) {
            setTimerActive(false);
        }
        return () => clearInterval(interval);
    }, [timerActive, timer]);

    // Lock Timer Effect
    useEffect(() => {
        let interval;
        if (locked && lockTimer > 0) {
            interval = setInterval(() => setLockTimer(prev => prev - 1), 1000);
        } else if (lockTimer === 0) {
            setLocked(false);
            setAttempts(0);
            setLockTimer(120);
        }
        return () => clearInterval(interval);
    }, [locked, lockTimer]);

    // Handle OAuth Transition
    useEffect(() => {
        if (oauthModal) {
            const timer = setTimeout(() => {
                const fakeEmail = oauthModal === 'google' ? 'user@gmail.com' : 'user@linkedin.com';
                setEmail(fakeEmail);
                setEmailValid(true);
                setOauthModal(null);
                setStep(2);
            }, 2000);
            return () => clearTimeout(timer);
        }
    }, [oauthModal]);

    // --- HANDLERS ---
    const validateEmail = (val) => {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        setEmailValid(regex.test(val));
        setEmail(val);
    };

    const nextStep = () => {
        setSlideDir("right");
        setStep(prev => prev + 1);
    };

    const prevStep = () => {
        setSlideDir("left");
        setStep(prev => prev - 1);
    };

    const triggerShake = () => {
        setShake(true);
        setTimeout(() => setShake(false), 500);
    };

    // --- RENDERING HELPERS (No hooks inside) ---
    const COLORS = {
        navyBg: 'linear-gradient(135deg, #0a0f1e 0%, #1a1f3e 50%, #0d1535 100%)',
        primary: '#2563eb',
        primaryDark: '#1d4ed8',
        success: '#22c55e',
        error: '#ef4444',
        warning: '#92400e',
        warningBg: '#fef9c3',
        warningBorder: '#fde68a',
        text: '#0f172a',
        muted: '#64748b',
        border: '#e2e8f0'
    };

    const isMobile = width < 640;

    // --- PARTIALS ---

    const renderStepIndicator = () => (
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', marginBottom: '32px' }}>
            {[1, 2, 3, 4].map(i => (
                <div key={i} style={{
                    width: '12px', height: '12px', borderRadius: '50%',
                    border: `2px solid ${i <= step ? 'transparent' : '#cbd5e1'}`,
                    backgroundColor: i < step ? COLORS.success : (i === step ? COLORS.primary : 'transparent'),
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.3s ease',
                    animation: i === step ? 'bioRing 2s infinite' : 'none',
                    color: '#fff', fontSize: '8px'
                }}>
                    {i < step ? '✓' : ''}
                </div>
            ))}
        </div>
    );

    const renderSecurityFooter = () => (
        <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginTop: '48px', opacity: 0.6, fontSize: '12px', color: COLORS.muted }}>
            <span>🔒 256-bit SSL</span>
            <span style={{ borderLeft: '1px solid #cbd5e1', paddingLeft: '16px' }}>🛡️ 2FA Protected</span>
            <span style={{ borderLeft: '1px solid #cbd5e1', paddingLeft: '16px' }}>✓ SOC 2 Certified</span>
        </div>
    );

    // --- STEP RENDERERS ---

    const renderStep1 = () => (
        <div style={{ animation: slideDir === 'right' ? 'slideLeft 0.4s forwards' : 'slideRight 0.4s forwards' }}>
            <h1 style={{ fontSize: '28px', fontWeight: '800', color: COLORS.text, marginBottom: '8px' }}>Welcome Back</h1>
            <p style={{ color: COLORS.muted, marginBottom: '32px' }}>Sign in to your account</p>

            {/* Email Input */}
            <div style={{ position: 'relative', marginBottom: '16px' }}>
                <input
                    type="text"
                    placeholder="Email or Username"
                    value={email}
                    onChange={e => validateEmail(e.target.value)}
                    autoFocus
                    style={{
                        width: '100%', padding: '16px', borderRadius: '12px',
                        border: `2px solid ${email ? (emailValid ? COLORS.success : COLORS.error) : COLORS.border}`,
                        outline: 'none', fontSize: '16px', transition: 'border-color 0.2s'
                    }}
                />
                {email && (
                    <div style={{ position: 'absolute', right: '16px', top: '18px', color: emailValid ? COLORS.success : COLORS.error }}>
                        {emailValid ? '✓' : '✕'}
                    </div>
                )}
            </div>

            {/* Social Buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
                <button
                    onClick={() => setOauthModal('google')}
                    style={{
                        width: '100%', padding: '14px', borderRadius: '12px', border: `2px solid ${COLORS.border}`,
                        backgroundColor: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px',
                        fontWeight: '600', transition: 'background 0.2s'
                    }}
                    onMouseOver={e => e.currentTarget.style.backgroundColor = '#f8fafc'}
                    onMouseOut={e => e.currentTarget.style.backgroundColor = '#fff'}
                >
                    <svg width="20" height="20" viewBox="0 0 24 24">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                    </svg>
                    Continue with Google
                </button>
                <button
                    onClick={() => setOauthModal('linkedin')}
                    style={{
                        width: '100%', padding: '14px', borderRadius: '12px', border: `2px solid #0a66c2`,
                        backgroundColor: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px',
                        fontWeight: '600', color: '#0a66c2'
                    }}
                >
                    <div style={{ width: '20px', height: '20px', backgroundColor: '#0a66c2', color: '#fff', borderRadius: '2px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px' }}>in</div>
                    Continue with LinkedIn
                </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                <div style={{ flex: 1, height: '1px', background: COLORS.border }} />
                <span style={{ fontSize: '13px', color: COLORS.muted }}>or continue with email</span>
                <div style={{ flex: 1, height: '1px', background: COLORS.border }} />
            </div>

            <button
                onClick={() => emailValid && nextStep()}
                disabled={!emailValid}
                style={{
                    width: '100%', padding: '16px', borderRadius: '12px', border: 'none',
                    background: emailValid ? `linear-gradient(135deg, ${COLORS.primary}, ${COLORS.primaryDark})` : '#cbd5e1',
                    color: '#fff', fontSize: '16px', fontWeight: 'bold', cursor: emailValid ? 'pointer' : 'default', transition: 'all 0.2s'
                }}
            >
                Continue
            </button>

            <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '14px' }}>
                <span style={{ color: COLORS.muted }}>Don't have an account? </span>
                <span style={{ color: COLORS.primary, fontWeight: 'bold', cursor: 'pointer' }}>Start free trial</span>
            </div>
            <div style={{ marginTop: '16px', textAlign: 'center', fontSize: '14px', color: COLORS.primary, fontWeight: 'bold', cursor: 'pointer' }}>
                Enterprise SSO →
            </div>
        </div>
    );

    const renderStep2 = () => (
        <div style={{ animation: 'slideLeft 0.4s forwards' }}>
            <h1 style={{ fontSize: '24px', fontWeight: '800', color: COLORS.text, marginBottom: '8px' }}>Choose verification</h1>
            <p style={{ color: COLORS.muted, marginBottom: '32px' }}>How would you like to verify your identity?</p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '32px' }}>
                <div
                    onClick={() => setMethod('password')}
                    style={{
                        padding: '20px', borderRadius: '16px', border: `2px solid ${method === 'password' ? COLORS.primary : COLORS.border}`,
                        backgroundColor: method === 'password' ? '#eff6ff' : '#fff', cursor: 'pointer', position: 'relative', transition: 'all 0.2s'
                    }}
                >
                    <div style={{ fontSize: '32px', marginBottom: '12px' }}>🔑</div>
                    <div style={{ fontWeight: 'bold', fontSize: '16px' }}>Password</div>
                    <div style={{ fontSize: '13px', color: COLORS.muted }}>Classic security</div>
                    {method === 'password' && <div style={{ position: 'absolute', bottom: '12px', right: '12px', color: COLORS.primary }}>✓</div>}
                </div>
                <div
                    onClick={() => setMethod('otp')}
                    style={{
                        padding: '20px', borderRadius: '16px', border: `2px solid ${method === 'otp' ? COLORS.primary : COLORS.border}`,
                        backgroundColor: method === 'otp' ? '#eff6ff' : '#fff', cursor: 'pointer', position: 'relative', transition: 'all 0.2s'
                    }}
                >
                    <div style={{ fontSize: '32px', marginBottom: '12px' }}>🔢</div>
                    <div style={{ fontWeight: 'bold', fontSize: '16px' }}>OTP Code</div>
                    <div style={{ fontSize: '13px', color: COLORS.muted }}>SMS or App</div>
                    {method === 'otp' && <div style={{ position: 'absolute', bottom: '12px', right: '12px', color: COLORS.primary }}>✓</div>}
                </div>
                <div
                    onClick={() => setMethod('pin')}
                    style={{
                        padding: '20px', borderRadius: '16px', border: `2px solid ${method === 'pin' ? COLORS.primary : COLORS.border}`,
                        backgroundColor: method === 'pin' ? '#eff6ff' : '#fff', cursor: 'pointer', position: 'relative', transition: 'all 0.2s'
                    }}
                >
                    <div style={{ fontSize: '32px', marginBottom: '12px' }}>🔐</div>
                    <div style={{ fontWeight: 'bold', fontSize: '16px' }}>6-Digit PIN</div>
                    <div style={{ fontSize: '13px', color: COLORS.muted }}>Personal code</div>
                    {method === 'pin' && <div style={{ position: 'absolute', bottom: '12px', right: '12px', color: COLORS.primary }}>✓</div>}
                </div>
                <div
                    onClick={() => setMethod('biometric')}
                    style={{
                        padding: '20px', borderRadius: '16px', border: `2px solid ${method === 'biometric' ? COLORS.primary : COLORS.border}`,
                        backgroundColor: method === 'biometric' ? '#eff6ff' : '#fff', cursor: 'pointer', position: 'relative', transition: 'all 0.2s'
                    }}
                >
                    <div style={{ position: 'absolute', top: '-10px', right: '10px', backgroundColor: COLORS.success, color: '#fff', fontSize: '10px', padding: '2px 8px', borderRadius: '10px', fontWeight: 'bold' }}>Recommended</div>
                    <div style={{ fontSize: '32px', marginBottom: '12px' }}>🪪</div>
                    <div style={{ fontWeight: 'bold', fontSize: '16px' }}>Biometric</div>
                    <div style={{ fontSize: '13px', color: COLORS.muted }}>Face ID</div>
                    {method === 'biometric' && <div style={{ position: 'absolute', bottom: '12px', right: '12px', color: COLORS.primary }}>✓</div>}
                </div>
            </div>

            <button
                onClick={() => nextStep()}
                style={{
                    width: '100%', padding: '16px', borderRadius: '12px', border: 'none',
                    background: `linear-gradient(135deg, ${COLORS.primary}, ${COLORS.primaryDark})`,
                    color: '#fff', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer'
                }}
            >
                Continue with {method}
            </button>
        </div>
    );

    const renderStep3A = () => {
        const strength = password.length === 0 ? 0 : (password.length < 4 ? 1 : (password.length < 8 ? 2 : (password.length < 12 ? 3 : 4)));
        const strengthLabels = ["", "Weak", "Fair", "Strong", "Very Strong"];
        const strengthColors = ["", COLORS.error, "#f97316", "#eab308", COLORS.success];

        const handleLogin = () => {
            if (password.length < 3) {
                triggerShake();
                setAttempts(a => a + 1);
                if (attempts + 1 >= 3) setLocked(true);
                return;
            }
            setTwoFAStep(true);
        };

        return (
            <div style={{ animation: 'slideLeft 0.4s forwards', transform: shake ? 'none' : 'none' }}>
                <div style={{ className: shake ? 'shake' : '' }}>
                    {newDevice && (
                        <div style={{ backgroundColor: COLORS.warningBg, border: `1px solid ${COLORS.warningBorder}`, color: COLORS.warning, padding: '12px', borderRadius: '12px', marginBottom: '24px', fontSize: '13px', fontWeight: '500' }}>
                            ⚠️ Logging in from a new device. Verify it's you.
                        </div>
                    )}

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '16px', backgroundColor: COLORS.primary, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>{email[0]?.toUpperCase()}</div>
                        <span style={{ fontSize: '14px', color: COLORS.text, fontWeight: '500' }}>{email}</span>
                    </div>

                    <h1 style={{ fontSize: '24px', fontWeight: '800', color: COLORS.text, marginBottom: '32px' }}>Enter your password</h1>

                    <div style={{ position: 'relative', marginBottom: '12px' }}>
                        <input
                            type={showPass ? "text" : "password"}
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            autoFocus
                            placeholder="Password"
                            style={{
                                width: '100%', padding: '16px 48px 16px 16px', borderRadius: '12px',
                                border: `2px solid ${COLORS.border}`, outline: 'none', fontSize: '16px'
                            }}
                        />
                        <button
                            onClick={() => setShowPass(!showPass)}
                            style={{ position: 'absolute', right: '16px', top: '16px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '18px' }}
                        >
                            {showPass ? '👁️' : '🔒'}
                        </button>
                    </div>

                    <div style={{ marginBottom: '24px' }}>
                        <div style={{ display: 'flex', gap: '4px', height: '4px', marginBottom: '8px' }}>
                            {[1, 2, 3, 4].map(i => (
                                <div key={i} style={{ flex: 1, background: i <= strength ? strengthColors[strength] : '#e2e8f0', borderRadius: '2px', transition: 'background 0.3s' }} />
                            ))}
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                            <span style={{ color: COLORS.muted }}>Strength: <span style={{ color: strengthColors[strength], fontWeight: 'bold' }}>{strengthLabels[strength]}</span></span>
                            <span style={{ color: COLORS.primary, fontWeight: 'bold', cursor: 'pointer' }}>Forgot password?</span>
                        </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
                        <span style={{ fontSize: '14px', color: COLORS.text }}>Trust this device for 30 days</span>
                        <div
                            onClick={() => setTrustDevice(!trustDevice)}
                            style={{
                                width: '44px', height: '24px', borderRadius: '22px', backgroundColor: trustDevice ? COLORS.primary : '#cbd5e1',
                                position: 'relative', cursor: 'pointer', transition: 'background 0.2s'
                            }}
                        >
                            <div style={{
                                width: '18px', height: '18px', borderRadius: '50%', backgroundColor: '#fff',
                                position: 'absolute', top: '3px', left: trustDevice ? '23px' : '3px', transition: 'left 0.2s'
                            }} />
                        </div>
                    </div>

                    {locked && (
                        <div style={{ color: COLORS.error, fontSize: '13px', textAlign: 'center', marginBottom: '16px', fontWeight: '500' }}>
                            Too many attempts. Try again in {lockTimer}s
                        </div>
                    )}

                    <button
                        onClick={handleLogin}
                        disabled={locked}
                        style={{
                            width: '100%', padding: '16px', borderRadius: '12px', border: 'none',
                            background: locked ? '#cbd5e1' : `linear-gradient(135deg, ${COLORS.primary}, ${COLORS.primaryDark})`,
                            color: '#fff', fontSize: '16px', fontWeight: 'bold', cursor: locked ? 'default' : 'pointer'
                        }}
                    >
                        Sign In
                    </button>
                </div>
            </div>
        );
    };

    const renderStep3B = () => {
        const handleOtpChange = (val, i) => {
            if (!/^\d*$/.test(val)) return;
            const newOtp = [...otp];
            newOtp[i] = val.slice(-1);
            setOtp(newOtp);
            if (val && i < 5) otpRefs[i + 1].current.focus();
        };

        const handleKeyDown = (e, i) => {
            if (e.key === 'Backspace' && !otp[i] && i > 0) otpRefs[i - 1].current.focus();
        };

        const handleVerify = () => {
            const code = otp.join("");
            if (code === "123456") {
                setSuccess(true);
                nextStep();
            } else {
                triggerShake();
                setOtp(["", "", "", "", "", ""]);
                otpRefs[0].current.focus();
            }
        };

        return (
            <div style={{ animation: 'slideLeft 0.4s forwards' }}>
                <h1 style={{ fontSize: '24px', fontWeight: '800', color: COLORS.text, marginBottom: '8px' }}>Verify your identity</h1>
                <p style={{ color: COLORS.muted, marginBottom: '40px' }}>Code sent to +91 ••••••7834</p>

                <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '40px' }}>
                    {otp.map((digit, i) => (
                        <input
                            key={i}
                            ref={otpRefs[i]}
                            type="text"
                            inputMode="numeric"
                            maxLength={1}
                            value={digit}
                            onChange={e => handleOtpChange(e.target.value, i)}
                            onKeyDown={e => handleKeyDown(e, i)}
                            style={{
                                width: '52px', height: '64px', borderRadius: '12px', border: `2px solid ${digit ? COLORS.primary : COLORS.border}`,
                                textAlign: 'center', fontSize: '24px', fontWeight: 'bold', outline: 'none',
                                backgroundColor: digit ? '#eff6ff' : '#fff', transition: 'all 0.2s',
                                boxShadow: digit ? '0 0 0 3px #bfdbfe' : 'none'
                            }}
                        />
                    ))}
                </div>

                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                    {timer > 0 ? (
                        <span style={{ color: COLORS.muted, fontSize: '14px' }}>Resend in 00:{timer < 10 ? `0${timer}` : timer}</span>
                    ) : (
                        <span style={{ color: COLORS.primary, fontWeight: 'bold', cursor: 'pointer' }} onClick={() => { setTimer(60); setTimerActive(true); }}>Resend code</span>
                    )}
                </div>

                <button
                    onClick={handleVerify}
                    style={{
                        width: '100%', padding: '16px', borderRadius: '12px', border: 'none',
                        background: `linear-gradient(135deg, ${COLORS.primary}, ${COLORS.primaryDark})`,
                        color: '#fff', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer'
                    }}
                >
                    Verify
                </button>
            </div>
        );
    };

    const renderStep3C = () => {
        const handleDigit = (d) => {
            if (pin.length < 6) {
                const newPin = [...pin, d];
                setPin(newPin);
                if (newPin.length === 6) {
                    if (newPin.join("") === "123456") {
                        setSuccess(true);
                        nextStep();
                    } else {
                        triggerShake();
                        setTimeout(() => setPin([]), 300);
                    }
                }
            }
        };

        return (
            <div style={{ animation: 'slideLeft 0.4s forwards' }}>
                <h1 style={{ fontSize: '24px', fontWeight: '800', color: COLORS.text, textAlign: 'center', marginBottom: '8px' }}>Enter your PIN</h1>
                <p style={{ color: COLORS.muted, textAlign: 'center', marginBottom: '40px' }}>Your 6-digit security PIN</p>

                <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginBottom: '48px' }}>
                    {[0, 1, 2, 3, 4, 5].map(i => (
                        <div key={i} style={{
                            width: '14px', height: '14px', borderRadius: '50%',
                            backgroundColor: pin.length > i ? COLORS.text : 'transparent',
                            border: `2px solid ${pin.length > i ? COLORS.text : '#cbd5e1'}`,
                            transition: 'all 0.1s'
                        }} />
                    ))}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', maxWidth: '280px', margin: '0 auto' }}>
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(d => (
                        <div key={d} onClick={() => handleDigit(d)} style={pinBtnStyle}>{d}</div>
                    ))}
                    <div onClick={() => { setMethod('biometric'); prevStep(); }} style={pinBtnStyle}>🪪</div>
                    <div onClick={() => handleDigit(0)} style={pinBtnStyle}>0</div>
                    <div onClick={() => setPin(pin.slice(0, -1))} style={pinBtnStyle}>⌫</div>
                </div>
            </div>
        );
    };

    const renderStep3D = () => {
        const startBio = () => {
            setBioState("scanning");
            setTimeout(() => setBioState("success"), 2000);
            setTimeout(() => { setSuccess(true); nextStep(); }, 2800);
        };

        return (
            <div style={{ animation: 'slideLeft 0.4s forwards', textAlign: 'center' }}>
                <h1 style={{ fontSize: '24px', fontWeight: '800', color: COLORS.text, marginBottom: '8px' }}>Biometric Authentication</h1>
                <p style={{ color: COLORS.muted, marginBottom: '48px' }}>Touch the sensor or look at camera</p>

                <div style={{ position: 'relative', width: '200px', height: '200px', margin: '0 auto 48px auto' }}>
                    {/* Animated Rings */}
                    <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: `2px solid ${bioState === 'success' ? COLORS.success : (bioState === 'failed' ? COLORS.error : COLORS.primary)}`, animation: 'bioRing 2s infinite', opacity: 0.2 }} />
                    <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: `2px solid ${bioState === 'success' ? COLORS.success : (bioState === 'failed' ? COLORS.error : COLORS.primary)}`, animation: 'bioRing 2s infinite', animationDelay: '0.6s', opacity: 0.2 }} />

                    <div style={{
                        position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%, -50%)',
                        width: '80px', height: '80px', borderRadius: '50%', backgroundColor: bioState === 'success' ? COLORS.success : (bioState === 'failed' ? COLORS.error : COLORS.primary),
                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '40px', color: '#fff'
                    }}>
                        {bioState === 'success' ? '✓' : (bioState === 'failed' ? '✗' : '👆')}
                    </div>
                </div>

                <p style={{ fontWeight: 'bold', marginBottom: '32px', color: bioState === 'success' ? COLORS.success : (bioState === 'failed' ? COLORS.error : COLORS.text) }}>
                    {bioState === 'idle' ? 'Ready to authenticate' : (bioState === 'scanning' ? 'Scanning... hold still' : (bioState === 'success' ? 'Identity verified ✓' : 'Failed. Try again'))}
                </p>

                <button
                    onClick={startBio}
                    disabled={bioState !== 'idle'}
                    style={{
                        width: '100%', padding: '16px', borderRadius: '12px', border: 'none',
                        background: bioState === 'idle' ? `linear-gradient(135deg, ${COLORS.primary}, ${COLORS.primaryDark})` : '#cbd5e1',
                        color: '#fff', fontSize: '16px', fontWeight: 'bold', cursor: bioState === 'idle' ? 'pointer' : 'default', marginBottom: '24px'
                    }}
                >
                    Authenticate
                </button>

                <div onClick={() => { setMethod('password'); prevStep(); }} style={{ color: COLORS.primary, fontSize: '14px', fontWeight: 'bold', cursor: 'pointer' }}>Use password instead</div>
                <div style={{ marginTop: '16px', fontSize: '11px', color: COLORS.muted }}>WebAuthn API available</div>
            </div>
        );
    };

    const renderSuccess = () => (
        <div style={{ textAlign: 'center', animation: 'fadeIn 0.6s forwards' }}>
            <div style={{ width: '100px', height: '100px', margin: '0 auto 32px auto', position: 'relative' }}>
                <svg viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="50" cy="50" r="45" stroke={COLORS.success} strokeWidth="6" fill="transparent" style={{ strokeDasharray: 283, strokeDashoffset: 0, transition: 'all 0.6s' }} />
                    <path d="M30 50 L45 65 L75 35" stroke={COLORS.success} strokeWidth="8" fill="none" strokeLinecap="round" style={{ strokeDasharray: 100, strokeDashoffset: 100, animation: 'drawCheck 0.6s 0.3s forwards' }} />
                </svg>
            </div>
            <h1 style={{ fontSize: '28px', fontWeight: '800', color: COLORS.text, marginBottom: '8px' }}>Authentication Successful!</h1>
            <p style={{ color: COLORS.muted, marginBottom: '32px' }}>Welcome back, {email}</p>

            <div style={{ width: '100%', height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden', marginBottom: '32px' }}>
                <div style={{ height: '100%', background: COLORS.success, animation: 'progressBar 2s linear forwards' }} />
            </div>

            <p style={{ fontSize: '14px', color: COLORS.muted, marginBottom: '16px' }}>Redirecting to dashboard...</p>
            <button style={{ width: '100%', padding: '16px', borderRadius: '12px', background: COLORS.success, color: '#fff', border: 'none', fontWeight: 'bold', opacity: 0.8 }}>→ Go to Dashboard</button>
        </div>
    );

    const pinBtnStyle = {
        width: '72px', height: '72px', borderRadius: '50%', backgroundColor: '#fff', border: `2px solid ${COLORS.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '22px', fontWeight: '600',
        cursor: 'pointer', transition: 'all 0.1s'
    };

    // --- OAUTH MODAL ---
    const renderOAuthModal = () => (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(8px)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ backgroundColor: '#fff', padding: '40px', borderRadius: '24px', width: '320px', textAlign: 'center', boxShadow: '0 20px 40px rgba(0,0,0,0.2)' }}>
                <div style={{ width: '60px', height: '60px', margin: '0 auto 24px auto', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8fafc', borderRadius: '16px' }}>
                    {oauthModal === 'google' ? (
                        <svg width="32" height="32" viewBox="0 0 24 24">
                            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
                            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                        </svg>
                    ) : (
                        <div style={{ width: '32px', height: '32px', background: '#0a66c2', color: '#fff', borderRadius: '4px', fontSize: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>in</div>
                    )}
                </div>
                <div style={{ fontWeight: '800', fontSize: '18px', marginBottom: '8px' }}>Connecting to {oauthModal === 'google' ? 'Google' : 'LinkedIn'}...</div>
                <p style={{ fontSize: '13px', color: COLORS.muted, marginBottom: '24px' }}>Securely authenticating your session</p>
                <div style={{ margin: '0 auto 24px auto', width: '32px', height: '32px', border: `3px solid ${COLORS.border}`, borderTopColor: COLORS.primary, borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                <div style={{ fontSize: '13px', color: COLORS.primary, cursor: 'pointer', fontWeight: 'bold' }} onClick={() => setOauthModal(null)}>Cancel</div>
            </div>
        </div>
    );

    // --- 2FA OVERLAY ---
    const renderTwoFA = () => {
        const handle2FAChange = (val, i) => {
            if (!/^\d*$/.test(val)) return;
            const newCode = [...twoFACode];
            newCode[i] = val.slice(-1);
            setTwoFACode(newCode);
            if (val && i < 5) twoFARefs[i + 1].current.focus();

            if (newCode.join("").length === 6) {
                if (newCode.join("") === "123456") {
                    setSuccess(true);
                    setTwoFAStep(false);
                    setStep(4);
                } else {
                    triggerShake();
                    setTwoFACode(["", "", "", "", "", ""]);
                    twoFARefs[0].current.focus();
                }
            }
        };

        return (
            <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)', zIndex: 90, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}>
                <div style={{ maxWidth: '420px', width: '100%', textAlign: 'center' }}>
                    <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: '#eff6ff', color: COLORS.primary, fontSize: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px auto' }}>🛡️</div>
                    <h1 style={{ fontSize: '24px', fontWeight: '800', color: COLORS.text, marginBottom: '8px' }}>Two-Factor Authentication</h1>
                    <p style={{ color: COLORS.muted, marginBottom: '40px' }}>Enter the 6-digit code from your app</p>

                    <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '40px' }}>
                        {twoFACode.map((digit, i) => (
                            <input
                                key={i} ref={twoFARefs[i]} type="text" inputMode="numeric" maxLength={1} value={digit}
                                onChange={e => handle2FAChange(e.target.value, i)}
                                onKeyDown={e => e.key === 'Backspace' && !twoFACode[i] && i > 0 && twoFARefs[i - 1].current.focus()}
                                style={{ width: '48px', height: '60px', borderRadius: '12px', border: `2px solid ${digit ? COLORS.primary : COLORS.border}`, textAlign: 'center', fontSize: '24px', fontWeight: 'bold', outline: 'none' }}
                            />
                        ))}
                    </div>

                    <div style={{ color: COLORS.primary, fontWeight: 'bold', fontSize: '14px', marginBottom: '32px', cursor: 'pointer' }}>Resend code (00:30)</div>
                    <div style={{ color: COLORS.muted, fontSize: '14px', cursor: 'pointer' }} onClick={() => setTwoFAStep(false)}>Use a different method</div>
                </div>
            </div>
        );
    };

    return (
        <div style={{ display: 'flex', height: '100vh', width: '100vw', backgroundColor: '#f8fafc', overflow: 'hidden', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
            <style>{`
        @keyframes slideLeft { from { transform: translateX(30px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes slideRight { from { transform: translateX(-30px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes bioRing { 0% { transform: scale(1); opacity: 0.6; } 100% { transform: scale(1.4); opacity: 0; } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes drawCheck { to { stroke-dashoffset: 0; } }
        @keyframes progressBar { from { width: 0; } to { width: 100%; } }
        @keyframes shake { 0%, 100% { transform: translateX(0); } 20% { transform: translateX(-8px); } 40% { transform: translateX(8px); } 60% { transform: translateX(-6px); } 80% { transform: translateX(6px); } }
        .shake { animation: shake 0.4s ease-in-out; }
      `}</style>

            {/* Brand Panel (Desktop) */}
            {!isMobile && (
                <div style={{ width: '42%', background: COLORS.navyBg, padding: '64px', position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                    {/* Dot Grid */}
                    <div style={{ position: 'absolute', inset: 0, opacity: 0.15, backgroundImage: `radial-gradient(circle, #fff 1px, transparent 1px)`, backgroundSize: '30px 30px' }} />

                    <div style={{ position: 'relative', zIndex: 1, marginBottom: 'auto' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '80px' }}>
                            <span style={{ fontSize: '32px' }}>🚀</span>
                            <span style={{ color: '#fff', fontSize: '24px', fontWeight: '800' }}>ProExport</span>
                        </div>
                        <h1 style={{ color: '#fff', fontSize: '48px', fontWeight: '800', lineHeight: 1.1, marginBottom: '48px' }}>AI-Powered Export Growth Engine</h1>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                            <Feature text="256-bit AES encrypted sessions" />
                            <Feature text="Zero-knowledge authentication" />
                            <Feature text="SOC 2 Type II compliant" />
                        </div>
                    </div>

                    <div style={{ position: 'relative', zIndex: 1, display: 'flex', gap: '24px', marginBottom: '32px' }}>
                        <div style={badgeStyle}>SSL</div>
                        <div style={badgeStyle}>ISO 27001</div>
                        <div style={badgeStyle}>GDPR</div>
                    </div>
                    <div style={{ position: 'relative', zIndex: 1, color: '#fff', opacity: 0.5, fontSize: '13px' }}>© 2025 ProExport. All rights reserved.</div>
                </div>
            )}

            {/* Auth Panel */}
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                {isMobile && (
                    <div style={{ position: 'absolute', top: 0, width: '100%', height: '60px', background: COLORS.navyBg, display: 'flex', alignItems: 'center', padding: '0 20px', gap: '10px' }}>
                        <span style={{ fontSize: '24px' }}>🚀</span>
                        <span style={{ color: '#fff', fontWeight: 'bold' }}>ProExport</span>
                    </div>
                )}

                <div style={{
                    maxWidth: '420px', width: '100%', padding: 'clamp(24px, 5vw, 42px)',
                    backgroundColor: '#fff', borderRadius: isMobile ? '0' : '32px',
                    boxShadow: isMobile ? 'none' : '0 10px 40px rgba(0,0,0,0.08)',
                    position: 'relative', className: shake ? 'shake' : ''
                }}>
                    {success ? renderSuccess() : (
                        <>
                            {step > 1 && (
                                <div
                                    onClick={prevStep}
                                    style={{ position: 'absolute', left: '24px', top: '42px', cursor: 'pointer', fontSize: '20px', color: COLORS.muted, zIndex: 10 }}
                                >←</div>
                            )}
                            {renderStepIndicator()}
                            {step === 1 && renderStep1()}
                            {step === 2 && renderStep2()}
                            {step === 3 && method === 'password' && renderStep3A()}
                            {step === 3 && method === 'otp' && renderStep3B()}
                            {step === 3 && method === 'pin' && renderStep3C()}
                            {step === 3 && method === 'biometric' && renderStep3D()}
                            {renderSecurityFooter()}
                        </>
                    )}
                </div>
            </div>

            {/* Overlays */}
            {oauthModal && renderOAuthModal()}
            {twoFAStep && renderTwoFA()}
        </div>
    );
}

const Feature = ({ text }) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ width: '24px', height: '24px', borderRadius: '50%', backgroundColor: '#22c55e', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px' }}>✓</div>
        <span style={{ color: '#fff', fontSize: '18px', fontWeight: '500' }}>{text}</span>
    </div>
);

const badgeStyle = {
    border: '1px solid rgba(255,255,255,0.3)', padding: '6px 16px', borderRadius: '20px', color: '#fff', fontSize: '12px', fontWeight: '600'
};
