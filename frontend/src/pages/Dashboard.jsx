import UserDashboard from "../components/Dashboard/UserDashboard";
import NavBar from "../components/Nav/NavBar";
import { USER_ROLES } from "../constants";

export default function Dashboard() {
  // TODO: fetch role from JWT token
  const userRole = 'user';

  return (
    <>
      <NavBar />
      <div style={{ paddingLeft: '32px', paddingRight: '32px' }}>
        { userRole === USER_ROLES.user 
          ? <UserDashboard /> 
          : null
        }
      </div>
    </>
  );
}