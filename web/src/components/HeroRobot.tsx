"use client";

export function HeroRobot() {
    return (
        <div className="group relative w-full h-auto cursor-pointer">
            <img
                alt="AI Robot Illustration"
                className="w-full h-auto object-contain relative z-10 drop-shadow-xl filter saturate-[0.8] transition-opacity duration-300 opacity-100 group-hover:opacity-0"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuAsp3nkRcPjUJSXxoHaBpp1Ar0Gi4PJMCZn-xJzzE6ahZ78wZb8_T6cgfpTzkBBeKTlHKw2APV-Wz0aD670qH3nSmxS4-YdI_5wmTGh54kksTQtgW2JuWW9MOymqmbj8KhqjwukaloUS7DoI1vB5-JfnGXR_ZigCSMgIwkleL734fQWFtC8bzlCBK1jVsobtqs6_e0-WKj7o7hUnbEuWkayND8rD5J5h10nDa0cVKfT__-DUJIRHhKgPdLqunSo4QOeU8aMei5Z-H8"
            />

            <video
                autoPlay
                loop
                muted
                playsInline
                className="w-full h-full object-contain absolute inset-0 z-10 drop-shadow-xl filter saturate-[0.8] transition-opacity duration-300 opacity-0 group-hover:opacity-100"
                src="/coreline_public_robot.mp4"
            />
        </div>
    );
}
