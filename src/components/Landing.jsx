import useMediaQuery from "../hooks/useMediaQuery";
import { motion } from "framer-motion";
import AnchorLink from "react-anchor-link-smooth-scroll";
import profile from "../assets/Images/Profile.webp";
import SocialMediaIcons from "../components/SocialMediaIcons";
import playIcon from "../assets/Icons/play.svg";
import pauseIcon from "../assets/Icons/pause.svg";
import PlayPauseButton from "../Utils/PlayPauseButton";
import cover from "../assets/Images/cover.jpg";

const Landing = ({ setSelectedPage }) => {
    const isAboveSmallScreens = useMediaQuery("(min-width: 768px)");


    return (
        <section id="home" className="md:flex md:justify-between md:items-center md:h-full gap-16">

            {/* Image Section */}

            <div className="md:order-2 flex justify-center basis-3/5 z-10 lg:mt-20">
                {isAboveSmallScreens ? (
                    <div className="relative z-0 ml-20 before:absolute before:-top-10 h-[420px] w-80 before:-left-10 before:rounded-t-[200px] before:w-full before:max-w-[2000px] before:max-h-[1200px] before:h-full before:border-2 before:border-bronze before:z-[-1]">
                        <img alt="" className="hover:filter hover:saturate-150 transition duration-500 z-10 rounded-t-full border-2 border-bronze" src={profile}/>
                    </div>
                ) : (
                    <div className="relative z-0 ml-4 before:absolute before:-top-5 before:-left-5 before:rounded-t-full before:w-full before:max-w-[400px] before:h-[365px] before:border before:border-bronze before:z-[-1] mt-16">
                        <img alt="" className="hover:filter hover:backdrop-saturate-150 transition duration-500 z-10 w-80 h-96 rounded-t-full border border-bronze" src={profile}/>
                    </div>
                )}
             </div>

            {/* Main Section */}
            <div className="z-30 basis-2/5 mt-5 md:mt-24">
                {/*Heading Section */}
                <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.5 }} transition={{ duration: 0.5 }} variants = {{ hidden: { opacity: 0, x: -50 }, visible: { opacity: 1, x: 0 }}} className="phone:mt-10 md:mt-0">
                    <p className="text-5xl md:text-7xl font-medium font-script z-10 text-orange-400 text-center md:text-start">Anurag Das</p>
                    <p className="mt-10 mb-7 text-center text-black font-outfit text-base font-medium md:text-start lg:text-lg">In the end, you have to just pull the trigger. Trust the car, trust the brakes, just go.</p>
                </motion.div>

                    {/*Call To Action */}

                <motion.div className="flex mt-5 justify-center md:justify-start" initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.5 }} transition={{ delay: 0.2, duration: 0.5 }} variants = {{ hidden: { opacity: 0, x: -50 }, visible: { opacity: 1, x: 0 }}}>
                    <AnchorLink className="text-black py-3 px-7 font-outfit font-medium transition duration-500 bg-white bg-opacity-50" onClick={() => setSelectedPage("contact")} href="#contact">
                        Contact Me
                    </AnchorLink>

                    <a className="rounded-r-sm py-0.5 pr-0.5" href="mailto:oeuvars@gmail.com">
                        <div className="bg-black hover:text-rose-700 transition duration-500 w-full h-full flex items-center justify-center font-playfair px-10 py-3 font-medium">
                            Let's Talk
                        </div>
                    </a>
                </motion.div>

                <motion.div className="flex mt-5 justify-center md:justify-start" initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.5 }} transition={{ delay: 0.4, duration: 0.5 }} variants = {{ hidden: { opacity: 0, x: -50 }, visible: { opacity: 1, x: 0 }}}>
                    <SocialMediaIcons />
                </motion.div>

                <motion.div className="bg-white text-black bg-opacity-50 border-2 border-black border-opacity-70 phone:px-7 lg:px-12 py-5 rounded-xl lg:mt-5 phone:mb-10 lg:mb-0 flex justify-between gap-3" initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.5 }} transition={{ delay: 0.2, duration: 0.5 }} variants = {{ hidden: { opacity: 0, x: -50 }, visible: { opacity: 1, x: 0 }}}>
                    <img src={cover} alt="cover" className="rounded-md w-16 h-16"/>
                    <div className="w-5/6 my-auto justify-start ml-2">
                        <h1 className="font-unbounded phone:text-base lg:text-lg">I Sip</h1>
                        <p className="font-unbounded phone:text-xs lg:text-sm text-bloodred">Tory Lanez</p>
                    </div>
                    <PlayPauseButton playIcon={playIcon} pauseIcon={pauseIcon}/>
                </motion.div>
            </div>
        </section>
    )
}

export default Landing;
