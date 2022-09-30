import ContactTracerDashboard from "../components/Dashboard/ContactTracerDashboard";
import NavBar from "../components/Nav/NavBar";
import { USER_ROLES } from "../constants";

export default function CTDashboard() {
  const userRole = 'contactTracer';

  return (
    <>
      <NavBar />
      <div style={{ paddingLeft: '32px', paddingRight: '32px' }}>
        { userRole === USER_ROLES.contactTracer 
          ? <ContactTracerDashboard /> 
          : null
        }
      </div>
    </>
  );
}