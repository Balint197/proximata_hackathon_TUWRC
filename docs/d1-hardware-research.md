# Hyundai D1 hardware: public evidence and remaining unknowns

Research date: 2026-11-13. Scope: public documentation only; no robot access, installs, bus probing, or firmware changes were performed.

## Conclusion

Public primary evidence establishes the sensor **classes** and a modular arrangement. It does not identify a LiDAR, depth-camera, computer, or motor-controller model, nor a usable drive protocol. Choose drivers only after identifying this event robot's actual devices. Ubuntu on the display is an event-specific fact from [the track brief](../tuwrc-d1-brief.md), not evidence that all peripherals terminate on that computer.

## Confirmed product description

| Item | What the source establishes | What it does not establish |
| --- | --- | --- |
| Navigation sensor | Hyundai calls it a 2D laser scanner; CBP calls it 2D LiDAR. [Hyundai brochure, printed p. 10](https://hyurobotics.com/wp-content/uploads/2022/11/220427_Service-Roboty-E16P-min.pdf#page=10), [CBP N334856](https://rulings.cbp.gov/ruling/N334856) | Manufacturer, model, field of view, scan rate, USB/Ethernet/serial transport, ROS driver. |
| Depth sensor | A 3D camera is listed; CBP places a 3D camera and touchscreen in an upper application module. [CBP N334856](https://rulings.cbp.gov/ruling/N334856) | RealSense, Orbbec, or any other brand; depth format, calibration, or SDK compatibility. |
| Controller/base | CBP lists a controller, motor, battery, LiDAR, disinfection module, and upper application module. [CBP N334856](https://rulings.cbp.gov/ruling/N334856) | Number of computers, CPU architecture, controller model, motor feedback, CAN/UART/USB protocol, or software topology. |
| Environmental sensing | Three fine-particle sensors plus ozone, CO₂, TVOC, temperature, and humidity sensing are described. [CBP N334856](https://rulings.cbp.gov/ruling/N334856) | Whether eight separately addressable devices exist, their part numbers, physical bus, units, or sampling protocol. |
| User interface | A 10.1-inch touch display, air-quality LED indicator, and voice interaction are advertised. [Hyundai brochure, printed p. 10](https://hyurobotics.com/wp-content/uploads/2022/11/220427_Service-Roboty-E16P-min.pdf#page=10) | Microphone/speaker model, audio access, LED commands, or an accessible voice API. |
| Physical platform | 58 × 58 × 129 cm and 74 kg. [CBP N334856](https://rulings.cbp.gov/ruling/N334856) | Wheel geometry, encoder scaling, kinematic model, or braking behavior. |

These are product descriptions, not measurements of this particular event unit. The CBP ruling dates to 6 September 2023.

## USB implications: hypotheses to test, not D1 specifications

The cited D1 materials do not say which sensors use USB or whether a display USB port exposes the robot's internal bus. Seeing Ubuntu and a connector does not establish access to the base controller. An internal peripheral could instead belong to another computer or an independent bus. This is an engineering inference from the missing topology information, not a discovered D1 wiring diagram.

When the team receives authorized access, record USB vendor/product IDs, product strings, interface classes, bound drivers, and port topology before selecting a package. A serial bridge identifies a transport adapter; it does not by itself identify the device connected behind it or its command language.

Linux's CDC ACM documentation distinguishes class-compliant interfaces from vendor-specific ones and shows driver binding and device descriptors as identification evidence. A `ttyACM` node therefore does not establish a motor protocol. Do not send the documentation's example modem commands to an unknown robot device. [Linux CDC ACM documentation](https://docs.kernel.org/usb/acm.html)

For cameras, UVC can include vendor-specific extension units; a standard video interface alone does not prove an accessible calibrated depth stream. Establish the actual model and formats before selecting a depth SDK. [Linux UVC driver documentation](https://docs.kernel.org/userspace-api/media/drivers/uvcvideo.html)

If a vendor application already operates a USB peripheral, Linux `usbmon` can collect host-side USB I/O traces. It does not decode a proprietary protocol automatically; traces reflect driver requests and can be incomplete. This is an option for a later, separately planned observation session, not an operation performed here. [Linux usbmon documentation](https://docs.kernel.org/usb/usbmon.html)

## Public-access search result and limits

The bounded search covered English/Korean D1 product terms, Hyundai service-robot pages, manual/API/ROS/GitHub terms, and candidate sensor manufacturers. No D1-specific public service manual, protocol specification, SDK, ROS package, or source repository was located. This is a search result, not proof that none exists. D-INFINITE D1 and other manufacturers' D1 robots are unrelated and must not supply this robot's specifications.

The manufacturer service-page URL `https://service.hyundai-robotics.com/product_descriptions/hyundai_d1` failed certificate hostname validation during retrieval; its current contents were not used. The brochure is Hyundai-authored material hosted on hyurobotics.com, not a service manual.

The browser text extractor could not retrieve CBP CROSS, but its public JSON endpoint returned the ruling successfully over HTTPS: [official CBP ruling data](https://rulings.cbp.gov/api/ruling/N334856). Thus the hardware claims above were checked against CBP directly rather than relying on third-party ruling mirrors.

## Most useful next evidence

Collect a host inventory and existing software/service configuration, exact device IDs, accessible board labels, and a cable/topology sketch. For each proposed driver, retain a chain from observed identity to the manufacturer's model documentation to the driver's supported hardware list. Treat LiDAR/depth/drive models and all motion packets as unknown until that chain exists. Preserve the brief's disconnected disinfection modules and no-firmware rule throughout identification.
