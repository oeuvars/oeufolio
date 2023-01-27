import useMediaQuery from "../hooks/useMediaQuery";
import { motion } from "framer-motion";
import AnchorLink from "react-anchor-link-smooth-scroll";
import pfp from "../assets/pfp.png";
import SocialMediaIcons from "../components/SocialMediaIcons";


const Landing = ({ setSelectedPage }) => {
    const isAboveMediumScreens = useMediaQuery("(min-width: 1060px)");

    return (
        <section id="home" className="md:flex md:justify-between md:items-center md:h-full gap-16 py-10 scale-110">

            {/* Image Section */}

            <div className="md:order-2 flex justify-center basis-3/5 z-10 mt-16 md:mt-32">
                {isAboveMediumScreens ? (
                    <div className="relative z-0 ml-20 before:absolute before:-top-24 before:-left-28 before:rounded-t-[400px] before:w-full before:max-w-[2000px] before:max-h-[1200px] before:h-full before:border-2 before:border-orange-800 scale-50 before:z-[-1]">
                        <img alt="" className="hover:filter hover:saturate-150 transition duration-500 z-10 w-full scale-125 max-w-[400px] md:max-w-[600px]" src={pfp}/>
                    </div>
                ) : (
                    <div className="relative z-0 ml-10 before:absolute before:-top-0 before:-left-10 before:rounded-t-[200px] before:w-full before:max-w-[400px] before:h-4/5 left-1 before:border-2 before:border-orange-800 before:z-[-1] scale-90 mt-5">
                        <img alt="" className="hover:filter hover:saturate-200 transition duration-500 z-10 w-full max-w-[400px] md:max-w-[600px] pr-1" src={pfp}/>
                    </div>
                )}
             </div>

            {/* Main Section */}
            <div className="z-30 basis-2/5 mt-12 md:mt-32">
                {/*Heading Section */}
                <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.5 }} transition={{ duration: 0.5 }} variants = {{ hidden: { opacity: 0, x: -50 }, visible: { opacity: 1, x: 0 }}}>
                    <p className="text-5xl md:text-6xl font-script z-10 text-princetonorange text-center md:text-start">Anurag {""} <span className="xs:relative xs:text-princetonorange xs:font-semibold z-20 sm:before:content-blebrush before:absolute before:-left-[25px] before:-top-[70px] before:z-[-1]">Das</span></p>
                    <p className="mt-10 mb-7 text-center text-black font-outfit text-base font-medium md:text-start lg:text-lg">In the end, you have to just pull the trigger. Trust the car, trust the brakes, just go.</p>
                </motion.div>

                    {/*Call To Action */}

                <motion.div className="flex mt-5 justify-center md:justify-start" initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.5 }} transition={{ delay: 0.2, duration: 0.5 }} variants = {{ hidden: { opacity: 0, x: -50 }, visible: { opacity: 1, x: 0 }}}>
                    <AnchorLink className="text-black hover:text-graylilac py-3 px-7 font-montserrat font-semibold transition duration-500" onClick={() => setSelectedPage("contact")} href="#contact">
                        Contact Me
                    </AnchorLink>

                    <AnchorLink className="rounded-r-sm py-0.5 pr-0.5" onClick={() => setSelectedPage("contact")} href="#contact">
                        <div className="bg-black hover:text-rose-700 transition duration-500 w-full h-full flex items-center justify-center font-playfair px-10">
                            Let's Talk.
                        </div>
                    </AnchorLink>
                </motion.div>

                <motion.div className="flex mt-5 justify-center md:justify-start" initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.5 }} transition={{ delay: 0.4, duration: 0.5 }} variants = {{ hidden: { opacity: 0, x: -50 }, visible: { opacity: 1, x: 0 }}}>
                    <SocialMediaIcons />
                </motion.div>
            </div>
        </section>
    )
}

export default Landing;
